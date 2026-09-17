import logging
from typing import Optional

from app.models.document import DocumentStatus

from app.processing.pipeline import (
    DocumentProcessingPipeline
)

from app.services.classification_service import (
    ClassificationService
)

from app.services.extraction_service import (
    ExtractionService
)

from app.services.validation_service import (
    ValidationService
)

from app.dedup.service import (
    DuplicateDetectionService
)

from app.anomaly.service import (
    AnomalyDetectionService
)

from app.services.duplicate_result_repository import (
    DuplicateResultRepository
)

from app.services.document_repository import (
    DocumentRepository
)


logger = logging.getLogger(__name__)


class DocumentProcessingService:

    def __init__(
        self,
        repository: DocumentRepository,
        pipeline: DocumentProcessingPipeline,
        classification_service: Optional[
            ClassificationService
        ] = None,
        extraction_service: Optional[
            ExtractionService
        ] = None,
        validation_service: Optional[
            ValidationService
        ] = None,
        duplicate_service: Optional[
            DuplicateDetectionService
        ] = None,
        duplicate_repository: Optional[
            DuplicateResultRepository
        ] = None,
        anomaly_service: Optional[
            AnomalyDetectionService
        ] = None,
    ):

        self.repository = repository

        self.pipeline = pipeline

        self.classification_service = (
            classification_service
        )

        self.extraction_service = (
            extraction_service
        )

        self.validation_service = (
            validation_service
        )

        self.duplicate_service = (
            duplicate_service
        )

        self.duplicate_repository = (
            duplicate_repository
        )

        self.anomaly_service = (
            anomaly_service
        )

    def process_document(
        self,
        document_id: str
    ):

        logger.info(
            "Starting document processing: %s",
            document_id
        )

        document = (
            self.repository.get_by_id(
                document_id
            )
        )

        if not document:

            logger.warning(
                "Document not found: %s",
                document_id
            )

            return

        self.repository.update_status(
            document_id,
            DocumentStatus.PROCESSING
        )

        try:

            content = self.pipeline.process(
                document
            )

            # --------------------------------
            # Classification (non-blocking)
            # --------------------------------

            classification_result = (
                self._classify_document(
                    document_id,
                    content.cleaned_text
                )
            )

            # --------------------------------
            # Extraction (non-blocking)
            # --------------------------------

            extraction_result = None

            if classification_result:
                extraction_result = (
                    self._extract_document(
                        document_id,
                        classification_result.document_type,
                        content.cleaned_text
                    )
                )

            # --------------------------------
            # Validation (non-blocking)
            # --------------------------------

            if (
                classification_result
                and extraction_result
            ):
                self._validate_document(
                    document_id,
                    classification_result.document_type,
                    extraction_result
                )

            self.repository.update_status(
                document_id,
                DocumentStatus.COMPLETED
            )

            # --------------------------------
            # Duplicate Detection (non-blocking)
            # --------------------------------

            self._detect_duplicates(document_id)

            # --------------------------------
            # Anomaly Detection (non-blocking)
            # --------------------------------

            self._detect_anomalies(document_id)

            logger.info(
                "Document processing completed: %s",
                document_id
            )

        except Exception:

            self.repository.update_status(
                document_id,
                DocumentStatus.FAILED
            )

            logger.exception(
                "Document processing failed: %s",
                document_id
            )

    def _classify_document(
        self,
        document_id: str,
        cleaned_text: str
    ):
        """
        Run classification on extracted text.

        This is non-blocking: if classification
        fails, the document processing still
        completes successfully.

        Returns:
            ClassificationResult or None.
        """

        if self.classification_service is None:

            logger.debug(
                "No classification service "
                "configured, skipping."
            )

            return None

        try:

            result = (
                self.classification_service
                .classify_document(
                    document_id=document_id,
                    document_text=cleaned_text
                )
            )

            logger.info(
                "Document %s classified: "
                "%s (%.4f)",
                document_id,
                result.document_type,
                result.confidence
            )

            return result

        except Exception:

            logger.exception(
                "Classification failed for "
                "document %s (non-blocking)",
                document_id
            )

            return None

    def _extract_document(
        self,
        document_id: str,
        document_type: str,
        cleaned_text: str
    ):
        """
        Run information extraction on text.

        This is non-blocking: if extraction fails,
        document processing still completes.

        Returns:
            ExtractionResult or None.
        """

        if self.extraction_service is None:

            logger.debug(
                "No extraction service "
                "configured, skipping."
            )

            return None

        try:

            result = (
                self.extraction_service
                .extract_document(
                    document_id=document_id,
                    document_type=document_type,
                    cleaned_text=cleaned_text
                )
            )

            if result:

                logger.info(
                    "Document %s extraction "
                    "completed: %d fields",
                    document_id,
                    len(result.fields)
                )

            return result

        except Exception:

            logger.exception(
                "Extraction failed for "
                "document %s (non-blocking)",
                document_id
            )

            return None

    def _validate_document(
        self,
        document_id: str,
        document_type: str,
        extraction_result
    ):
        """
        Run validation on extracted fields.

        This is non-blocking: if validation fails,
        document processing still completes.
        """

        if self.validation_service is None:

            logger.debug(
                "No validation service "
                "configured, skipping."
            )

            return

        try:

            # Convert ExtractionResult to the
            # field dict format expected by rules
            extracted_fields = (
                extraction_result.to_dict()
                .get("fields", {})
            )

            result = (
                self.validation_service
                .validate_document(
                    document_id=document_id,
                    document_type=document_type,
                    extracted_fields=(
                        extracted_fields
                    )
                )
            )

            if result:

                logger.info(
                    "Document %s validation: "
                    "%s (%d rules, %d errors)",
                    document_id,
                    result.status.value,
                    len(result.results),
                    len(result.errors)
                )

        except Exception:

            logger.exception(
                "Validation failed for "
                "document %s (non-blocking)",
                document_id
            )

    def _detect_duplicates(
        self,
        document_id: str
    ):
        """
        Run duplicate detection against existing completed documents.

        This is non-blocking: if duplicate detection fails,
        document processing still completes successfully.
        """

        if self.duplicate_service is None:

            logger.debug(
                "No duplicate detection service "
                "configured, skipping."
            )

            return

        try:

            result = (
                self.duplicate_service
                .check_document(document_id)
            )

            if result and result.matches:

                if self.duplicate_repository:

                    self.duplicate_repository.save_matches([
                        m.to_dict()
                        for m in result.matches
                    ])

                logger.info(
                    "Document %s duplicate check: "
                    "%d matches (%d exact, %d near)",
                    document_id,
                    len(result.matches),
                    len(result.exact_matches),
                    len(result.near_matches),
                )

        except Exception:

            logger.exception(
                "Duplicate detection failed for "
                "document %s (non-blocking)",
                document_id
            )

    def _detect_anomalies(
        self,
        document_id: str
    ):
        """
        Run anomaly detection on extracted document features.

        This is non-blocking: if anomaly detection fails,
        document processing remains completed.
        """

        if self.anomaly_service is None:

            logger.debug(
                "No anomaly detection service "
                "configured, skipping."
            )

            return

        try:

            result = (
                self.anomaly_service
                .check_document(
                    document_id=document_id,
                    persist=True,
                )
            )

            if result:

                logger.info(
                    "Document %s anomaly check: "
                    "is_anomaly=%s (score=%.4f)",
                    document_id,
                    result.is_anomaly,
                    result.anomaly_score,
                )

        except Exception:

            logger.exception(
                "Anomaly detection failed for "
                "document %s (non-blocking)",
                document_id
            )