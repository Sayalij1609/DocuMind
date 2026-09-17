"""
Unit and integration tests for Phase 9 — Document Anomaly Detection.

Tests:
- DocumentFeatureExtractor on complete and missing data
- IsolationForestDetector on normal records
- IsolationForestDetector on synthetic extreme outliers
- Missing value imputation and flag tracking
- Insufficient training data handling
- Model serialization, persistence, and reloading
- AnomalyDetectionService end-to-end inference
- AnomalyResultRepository upsert and retrieval
- Terminology check (unusual / outlier, non-fraud)
"""

import os
from datetime import datetime, timezone
import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.anomaly.base import (
    AnomalyResult,
    FeatureVector,
)
from app.anomaly.features import (
    DocumentFeatureExtractor,
    FEATURE_NAMES,
    EXPECTED_INVOICE_FIELDS,
)
from app.anomaly.isolation_forest import (
    IsolationForestDetector,
)
from app.anomaly.service import (
    AnomalyDetectionService,
)
from app.database.base import Base
from app.models.anomaly_result import AnomalyResultModel
from app.models.document import Document, DocumentStatus
from app.models.document_content import DocumentContent
from app.models.duplicate_result import DuplicateResultModel
from app.models.extraction_result import ExtractionResultModel
from app.models.validation_result import ValidationResultModel
from app.services.anomaly_result_repository import (
    AnomalyResultRepository,
)


# ====================================================
# Feature Extractor Tests
# ====================================================

class TestDocumentFeatureExtractor:

    def test_extract_complete_invoice(self):
        extractor = DocumentFeatureExtractor()

        doc_content = DocumentContent(
            document_id="doc-101",
            raw_text="Tax Invoice Acme Corp Total 1000",
            cleaned_text="Tax Invoice Acme Corp Total 1000 Subtotal 850 Tax 150",
            extraction_method="tesseract",
            page_count=2,
        )

        extraction_rec = ExtractionResultModel(
            document_id="doc-101",
            document_type="invoice",
            extracted_fields={
                "vendor": {"value": "Acme Corp"},
                "invoice_number": {"value": "INV-001"},
                "invoice_date": {"value": "2026-09-01"},
                "subtotal": {"value": "850.00"},
                "tax": {"value": "150.00"},
                "total": {"value": "1000.00"},
            },
        )

        validation_rec = ValidationResultModel(
            document_id="doc-101",
            document_type="invoice",
            status="VALID",
            rule_results=[
                {"rule_code": "REQUIRED_FIELDS", "status": "PASS"},
                {"rule_code": "TOTAL_MISMATCH", "status": "PASS"},
            ],
        )

        duplicate_matches = [
            {"similarity_score": 0.12},
        ]

        fv = extractor.extract(
            document_id="doc-101",
            content=doc_content,
            extraction_record=extraction_rec,
            validation_record=validation_rec,
            duplicate_matches=duplicate_matches,
            vendor_frequency_lookup=lambda v: 5,
        )

        assert fv.document_id == "doc-101"
        assert fv.values["invoice_amount"] == 1000.0
        assert fv.missing_flags["invoice_amount"] is False

        # tax_percentage = (150 / 850) * 100 = 17.65%
        assert 17.6 <= fv.values["tax_percentage"] <= 17.7
        assert fv.missing_flags["tax_percentage"] is False

        assert fv.values["page_count"] == 2.0
        assert fv.values["missing_field_count"] == 0.0
        assert fv.values["duplicate_similarity"] == 0.12
        assert fv.values["vendor_frequency"] == 5.0
        assert fv.values["validation_error_count"] == 0.0
        assert fv.values["item_count"] == 0.0
        assert fv.missing_flags["item_count"] is True

    def test_extract_missing_fields_graceful(self):
        """Extractor must handle empty / missing records without error."""
        extractor = DocumentFeatureExtractor()

        fv = extractor.extract(
            document_id="doc-empty",
            content=None,
            extraction_record=None,
            validation_record=None,
            duplicate_matches=None,
        )

        assert fv.document_id == "doc-empty"
        assert fv.values["invoice_amount"] == 0.0
        assert fv.missing_flags["invoice_amount"] is True
        assert fv.values["tax_percentage"] == 0.0
        assert fv.missing_flags["tax_percentage"] is True
        assert fv.values["document_length"] == 0.0
        assert fv.missing_flags["document_length"] is True
        assert fv.values["missing_field_count"] == float(len(EXPECTED_INVOICE_FIELDS))
        assert fv.values["duplicate_similarity"] == 0.0
        assert fv.values["validation_error_count"] == 0.0

        # Vector conversion must produce numerical array with no NaNs
        arr = fv.to_array()
        assert len(arr) == len(FEATURE_NAMES)
        assert all(isinstance(x, (int, float)) for x in arr)
        assert not any(np.isnan(arr))


# ====================================================
# Isolation Forest Unit Tests
# ====================================================

class TestIsolationForestDetector:

    @pytest.fixture
    def baseline_detector(self):
        """Pre-fitted baseline detector."""
        return IsolationForestDetector.create_synthetic_baseline(
            n_samples=60,
            contamination=0.05,
            random_state=42,
        )

    def test_normal_records_classified_as_inliers(self, baseline_detector):
        """A standard normal invoice should not be flagged as an anomaly."""
        normal_fv = FeatureVector(
            document_id="normal-1",
            values={
                "invoice_amount": 1500.0,
                "tax_percentage": 10.0,
                "document_length": 1400.0,
                "word_count": 200.0,
                "page_count": 1.0,
                "missing_field_count": 0.0,
                "duplicate_similarity": 0.05,
                "vendor_frequency": 6.0,
                "validation_error_count": 0.0,
                "item_count": 0.0,
            },
            feature_names=list(FEATURE_NAMES),
        )

        is_anomaly, anomaly_score, decision_score = (
            baseline_detector.predict(normal_fv)
        )

        assert is_anomaly is False
        assert decision_score > 0.0  # Positive decision function indicates inlier

    def test_synthetic_extreme_outliers_detected(self, baseline_detector):
        """An extreme outlier (e.g. $500,000,000 invoice with 100 validation errors)
        must be flagged as anomalous with negative decision score."""
        extreme_fv = FeatureVector(
            document_id="extreme-outlier",
            values={
                "invoice_amount": 500_000_000.0,  # Extreme amount
                "tax_percentage": 99.0,           # Extreme tax
                "document_length": 500_000.0,     # Massive document
                "word_count": 80_000.0,
                "page_count": 450.0,
                "missing_field_count": 6.0,
                "duplicate_similarity": 0.98,
                "vendor_frequency": 0.0,
                "validation_error_count": 25.0,
                "item_count": 0.0,
            },
            feature_names=list(FEATURE_NAMES),
        )

        is_anomaly, anomaly_score, decision_score = (
            baseline_detector.predict(extreme_fv)
        )

        assert is_anomaly is True
        assert decision_score < 0.0  # Negative decision function indicates outlier
        assert anomaly_score > 0.0

    def test_insufficient_training_data_raises_error(self):
        """Fitting with fewer samples than min_samples must raise ValueError."""
        detector = IsolationForestDetector(min_samples=10)
        few_vectors = [
            FeatureVector(
                document_id=f"doc-{i}",
                values={name: 1.0 for name in FEATURE_NAMES},
                feature_names=list(FEATURE_NAMES),
            )
            for i in range(5)
        ]

        with pytest.raises(ValueError, match="Insufficient training data"):
            detector.fit(few_vectors)

    def test_unfitted_detector_raises_error_on_predict(self):
        """Calling predict before fitting must raise RuntimeError."""
        detector = IsolationForestDetector()
        fv = FeatureVector(
            document_id="test",
            values={name: 1.0 for name in FEATURE_NAMES},
            feature_names=list(FEATURE_NAMES),
        )
        with pytest.raises(RuntimeError, match="not fitted"):
            detector.predict(fv)

    def test_model_persistence_and_reloading(self, baseline_detector, tmp_path):
        """Model must save to disk and reload identically."""
        model_file = str(tmp_path / "iso_forest.joblib")
        baseline_detector.save(model_file)
        assert os.path.exists(model_file)

        # Load into new detector
        new_detector = IsolationForestDetector()
        new_detector.load(model_file)
        assert new_detector.is_fitted is True

        test_fv = FeatureVector(
            document_id="test-persistence",
            values={
                "invoice_amount": 2500.0,
                "tax_percentage": 15.0,
                "document_length": 1200.0,
                "word_count": 180.0,
                "page_count": 1.0,
                "missing_field_count": 0.0,
                "duplicate_similarity": 0.0,
                "vendor_frequency": 3.0,
                "validation_error_count": 0.0,
                "item_count": 0.0,
            },
            feature_names=list(FEATURE_NAMES),
        )

        orig_anomaly, orig_score, orig_decision = (
            baseline_detector.predict(test_fv)
        )
        loaded_anomaly, loaded_score, loaded_decision = (
            new_detector.predict(test_fv)
        )

        assert orig_anomaly == loaded_anomaly
        assert np.isclose(orig_score, loaded_score)
        assert np.isclose(orig_decision, loaded_decision)


# ====================================================
# Repository & Service Tests (In-Memory SQLite)
# ====================================================

@pytest.fixture
def db_session():
    """In-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestAnomalyResultRepository:

    def test_save_and_retrieve_result(self, db_session):
        now = datetime.now(timezone.utc)
        doc = Document(
            document_id="doc-anom-1",
            filename="invoice.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="uploads/invoice.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        db_session.add(doc)
        db_session.commit()

        repo = AnomalyResultRepository(db_session)
        result = AnomalyResult(
            document_id="doc-anom-1",
            is_anomaly=True,
            anomaly_score=0.2845,
            decision_function_score=-0.2845,
            features={"invoice_amount": 999999.0},
            model_version="isolation_forest_v1",
            detected_at=now,
        )

        saved = repo.save_result(result)
        assert saved.document_id == "doc-anom-1"
        assert saved.is_anomaly is True
        assert saved.anomaly_score == 0.2845

        # Retrieve
        fetched = repo.get_by_document_id("doc-anom-1")
        assert fetched is not None
        assert fetched.is_anomaly is True
        assert fetched.features["invoice_amount"] == 999999.0

    def test_upsert_updates_existing_record(self, db_session):
        now = datetime.now(timezone.utc)
        doc = Document(
            document_id="doc-upsert",
            filename="invoice.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="uploads/invoice.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        db_session.add(doc)
        db_session.commit()

        repo = AnomalyResultRepository(db_session)
        r1 = AnomalyResult(
            document_id="doc-upsert",
            is_anomaly=False,
            anomaly_score=-0.15,
            decision_function_score=0.15,
            features={"invoice_amount": 1000.0},
        )
        repo.save_result(r1)

        # Update with new evaluation
        r2 = AnomalyResult(
            document_id="doc-upsert",
            is_anomaly=True,
            anomaly_score=0.35,
            decision_function_score=-0.35,
            features={"invoice_amount": 500000.0},
        )
        repo.save_result(r2)

        fetched = repo.get_by_document_id("doc-upsert")
        assert fetched.is_anomaly is True
        assert fetched.anomaly_score == 0.35


class TestAnomalyDetectionService:

    def test_service_check_document_end_to_end(self, db_session, tmp_path):
        now = datetime.now(timezone.utc)
        model_path = str(tmp_path / "model.joblib")

        doc = Document(
            document_id="doc-service-1",
            filename="service_inv.pdf",
            file_type="pdf",
            file_size=2048,
            file_path="uploads/service_inv.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        content = DocumentContent(
            document_id="doc-service-1",
            raw_text="Tax Invoice Corp Total 1200",
            cleaned_text="Tax Invoice Corp Total 1200 Subtotal 1000 Tax 200",
            extraction_method="tesseract",
            page_count=1,
        )
        extraction = ExtractionResultModel(
            document_id="doc-service-1",
            document_type="invoice",
            extracted_fields={
                "vendor": {"value": "Tech Corp"},
                "invoice_number": {"value": "INV-789"},
                "total": {"value": "1200.00"},
                "subtotal": {"value": "1000.00"},
                "tax": {"value": "200.00"},
            },
        )
        db_session.add_all([doc, content, extraction])
        db_session.commit()

        service = AnomalyDetectionService(
            session=db_session,
            model_path=model_path,
        )

        res = service.check_document("doc-service-1", persist=True)

        assert res.document_id == "doc-service-1"
        assert isinstance(res.is_anomaly, bool)
        assert isinstance(res.anomaly_score, float)
        assert "invoice_amount" in res.features
        assert res.features["invoice_amount"] == 1200.0

        # Verify saved in DB
        repo = AnomalyResultRepository(db_session)
        saved = repo.get_by_document_id("doc-service-1")
        assert saved is not None
        assert saved.document_id == "doc-service-1"

    def test_terminology_does_not_assert_fraud(self, db_session, tmp_path):
        """Verify that results do not contain fraud claims."""
        service = AnomalyDetectionService(
            session=db_session,
            model_path=str(tmp_path / "model.joblib"),
        )
        res = service.check_document("non-existent-doc", persist=False)
        d = res.to_dict()

        # Keys must strictly use anomaly/outlier concepts
        assert "is_anomaly" in d
        assert "anomaly_score" in d
        assert "fraud" not in str(d).lower()
