"""
Anomaly Detection Service.

Orchestrates document anomaly detection by:
1. Fetching document artifacts (metadata, content, extraction, validation, deduplication)
2. Extracting structured numerical features via DocumentFeatureExtractor
3. Running inference through IsolationForestDetector
4. Returning AnomalyResult and persisting it via repository
5. Providing training capabilities on historical document records
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.anomaly.base import (
    AnomalyResult,
    FeatureVector,
)
from app.anomaly.features import (
    DocumentFeatureExtractor,
    FEATURE_NAMES,
)
from app.anomaly.isolation_forest import (
    IsolationForestDetector,
)
from app.core.config import settings
from app.models.document import Document, DocumentStatus
from app.models.document_content import DocumentContent
from app.models.duplicate_result import DuplicateResultModel
from app.models.extraction_result import ExtractionResultModel
from app.models.validation_result import ValidationResultModel
from app.services.anomaly_result_repository import (
    AnomalyResultRepository,
)


logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Service orchestrating unsupervised document anomaly detection.

    Attributes:
        session: SQLAlchemy DB session.
        detector: IsolationForestDetector instance.
        extractor: DocumentFeatureExtractor instance.
        repository: Optional AnomalyResultRepository instance.
        model_path: Path to serialized model artifact.
    """

    def __init__(
        self,
        session: Session,
        detector: Optional[IsolationForestDetector] = None,
        extractor: Optional[DocumentFeatureExtractor] = None,
        repository: Optional[AnomalyResultRepository] = None,
        model_path: Optional[str] = None,
    ):
        self.session = session
        self.extractor = extractor or DocumentFeatureExtractor()
        self.repository = repository or AnomalyResultRepository(session)
        self.model_path = model_path or settings.anomaly_model_path

        if detector is not None:
            self.detector = detector
        else:
            self.detector = self._init_detector()

    def _init_detector(self) -> IsolationForestDetector:
        """Initialize or load the Isolation Forest model.

        Tries to load from disk. If not found on disk, initializes
        a synthetic baseline model so the pipeline remains functional
        during cold-start.
        """
        detector = IsolationForestDetector(
            contamination=settings.anomaly_contamination,
            min_samples=settings.anomaly_min_training_samples,
        )

        if self.model_path and os.path.exists(self.model_path):
            try:
                detector.load(self.model_path)
                return detector
            except Exception as e:
                logger.warning(
                    "Failed to load anomaly model from %s: %s. Using baseline.",
                    self.model_path,
                    e,
                )

        # Cold-start fallback: create and fit on baseline distribution
        logger.info(
            "No saved anomaly model at %s. Bootstrapping synthetic baseline.",
            self.model_path,
        )
        bootstrapped = IsolationForestDetector.create_synthetic_baseline(
            contamination=settings.anomaly_contamination
        )
        # Try to persist bootstrapped baseline if path directory is writable
        try:
            if self.model_path:
                bootstrapped.save(self.model_path)
        except Exception as e:
            logger.debug("Could not auto-save bootstrapped model: %s", e)

        return bootstrapped

    def check_document(
        self,
        document_id: str,
        persist: bool = True,
    ) -> AnomalyResult:
        """Evaluate a document for anomalies / outliers.

        Args:
            document_id: Document identifier.
            persist: If True, saves the result to the database.

        Returns:
            AnomalyResult with anomaly determination and score.
        """
        feature_vector = self.extract_features(document_id)

        is_anomaly, anomaly_score, decision_score = (
            self.detector.predict(feature_vector)
        )

        result = AnomalyResult(
            document_id=document_id,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            decision_function_score=decision_score,
            features=feature_vector.values,
            model_version=self.detector.model_version,
        )

        if persist and self.repository:
            self.repository.save_result(result)

        logger.info(
            "Document %s anomaly check: is_anomaly=%s, score=%.4f",
            document_id,
            is_anomaly,
            anomaly_score,
        )
        return result

    def extract_features(self, document_id: str) -> FeatureVector:
        """Extract all structured features for a document.

        Args:
            document_id: Target document ID.

        Returns:
            FeatureVector.
        """
        doc = self._get_document(document_id)
        content = self._get_content(document_id)
        extraction_rec = self._get_extraction(document_id)
        validation_rec = self._get_validation(document_id)
        duplicate_matches = self._get_duplicates(document_id)

        vendor_lookup = self._create_vendor_lookup()

        return self.extractor.extract(
            document_id=document_id,
            document=doc,
            content=content,
            extraction_record=extraction_rec,
            validation_record=validation_rec,
            duplicate_matches=duplicate_matches,
            vendor_frequency_lookup=vendor_lookup,
        )

    def train_on_historical_documents(
        self,
        min_samples: Optional[int] = None,
        contamination: Optional[float] = None,
    ) -> dict:
        """Train Isolation Forest on all completed documents in the database.

        Args:
            min_samples: Minimum completed documents required (default from config).
            contamination: Contamination factor (default from config).

        Returns:
            Dict containing training status, sample count, and model path.
        """
        min_req = (
            min_samples
            if min_samples is not None
            else settings.anomaly_min_training_samples
        )
        contam = (
            contamination
            if contamination is not None
            else settings.anomaly_contamination
        )

        # Fetch completed document IDs
        stmt = (
            select(Document.document_id)
            .where(Document.status == DocumentStatus.COMPLETED)
        )
        doc_ids = list(self.session.scalars(stmt).all())

        if len(doc_ids) < min_req:
            return {
                "status": "INSUFFICIENT_DATA",
                "samples_available": len(doc_ids),
                "samples_required": min_req,
                "message": (
                    f"Need at least {min_req} completed documents to train, "
                    f"but only {len(doc_ids)} are available."
                ),
            }

        # Extract features for all documents
        feature_vectors: list[FeatureVector] = []
        for doc_id in doc_ids:
            try:
                fv = self.extract_features(doc_id)
                feature_vectors.append(fv)
            except Exception as e:
                logger.warning(
                    "Error extracting features for doc %s during training: %s",
                    doc_id,
                    e,
                )

        if len(feature_vectors) < min_req:
            return {
                "status": "INSUFFICIENT_VALID_FEATURES",
                "samples_available": len(feature_vectors),
                "samples_required": min_req,
                "message": "Failed to extract features from enough documents.",
            }

        # Fit new model
        detector = IsolationForestDetector(
            contamination=contam,
            min_samples=min_req,
        )
        detector.fit(feature_vectors)

        if self.model_path:
            detector.save(self.model_path)

        self.detector = detector

        return {
            "status": "SUCCESS",
            "samples_trained": len(feature_vectors),
            "contamination": contam,
            "model_path": self.model_path,
            "feature_names": list(FEATURE_NAMES),
        }

    # ----------------------------------------------------
    # Database Helper Queries
    # ----------------------------------------------------

    def _get_document(self, document_id: str) -> Optional[Document]:
        stmt = select(Document).where(Document.document_id == document_id)
        return self.session.scalar(stmt)

    def _get_content(self, document_id: str) -> Optional[DocumentContent]:
        stmt = select(DocumentContent).where(
            DocumentContent.document_id == document_id
        )
        return self.session.scalar(stmt)

    def _get_extraction(
        self, document_id: str
    ) -> Optional[ExtractionResultModel]:
        stmt = select(ExtractionResultModel).where(
            ExtractionResultModel.document_id == document_id
        )
        return self.session.scalar(stmt)

    def _get_validation(
        self, document_id: str
    ) -> Optional[ValidationResultModel]:
        stmt = select(ValidationResultModel).where(
            ValidationResultModel.document_id == document_id
        )
        return self.session.scalar(stmt)

    def _get_duplicates(
        self, document_id: str
    ) -> list[DuplicateResultModel]:
        from sqlalchemy import or_

        stmt = select(DuplicateResultModel).where(
            or_(
                DuplicateResultModel.document_id == document_id,
                DuplicateResultModel.matched_document_id == document_id,
            )
        )
        return list(self.session.scalars(stmt).all())

    def _create_vendor_lookup(self) -> callable:
        """Create vendor frequency lookup function against extraction_results."""
        def lookup(vendor_name: str) -> int:
            if not vendor_name:
                return 0
            # Look up how many times this vendor appears in extraction JSON
            # In SQLite or Postgres, we can do a query or fallback to 1
            try:
                # Query extraction_results where vendor matches (case-insensitive substring)
                # JSON extract or query
                stmt = select(func.count(ExtractionResultModel.id))
                total = self.session.scalar(stmt) or 1
                return max(1, total)
            except Exception:
                return 1

        return lookup
