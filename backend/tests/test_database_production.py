"""
Unit and integration tests for Phase 10 — Production Database Design.

Validates:
- Instantiation and persistence of all 11 production models
- Bidirectional ORM relationship traversal
- Cascading delete of document child records
- Set-null foreign key behavior on user deletion
- Unique constraints (user email, model metadata version, duplicate pair)
- Indexed search queries for documents and extraction results
- ExtractionResultRepository indexed column extraction and lookup
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.document import Document, DocumentStatus
from app.models.document_content import DocumentContent
from app.models.document_page import DocumentPage
from app.models.classification_result import ClassificationResultModel
from app.models.extraction_result import ExtractionResultModel
from app.models.validation_result import ValidationResultModel
from app.models.duplicate_result import DuplicateResultModel
from app.models.anomaly_result import AnomalyResultModel
from app.models.user import UserModel
from app.models.document_review import DocumentReviewModel
from app.models.model_metadata import ModelMetadataModel
from app.services.extraction_result_repository import ExtractionResultRepository


@pytest.fixture
def db_session():
    """In-memory SQLite session with foreign keys enabled."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# ====================================================
# Model Persistence & Field Storage Tests
# ====================================================

class TestProductionModelPersistence:

    def test_persist_all_eleven_models(self, db_session):
        now = datetime.now(timezone.utc)

        # 1. User
        user = UserModel(
            id="usr-001",
            email="auditor@nexora.io",
            hashed_password="argon2_hashed_secret",
            full_name="Nexora Auditor",
            role="reviewer",
            is_active=True,
        )
        db_session.add(user)

        # 2. Document
        doc = Document(
            document_id="doc-prod-001",
            user_id="usr-001",
            filename="invoice_2026.pdf",
            file_type="pdf",
            file_size=4096,
            file_path="uploads/invoice_2026.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            classification_confidence=0.98,
            classified_at=now,
            created_at=now,
            updated_at=now,
        )
        db_session.add(doc)

        # 3. Document Content
        content = DocumentContent(
            document_id="doc-prod-001",
            raw_text="INVOICE 101 Acme Corp Total: $500",
            cleaned_text="invoice 101 acme corp total 500",
            extraction_method="tesseract",
            page_count=1,
        )
        db_session.add(content)

        # 4. Document Page
        page = DocumentPage(
            document_id="doc-prod-001",
            page_number=1,
            raw_text="INVOICE 101",
            cleaned_text="invoice 101",
            extraction_method="tesseract",
            image_path="pages/doc-prod-001_p1.png",
            image_width=800,
            image_height=1000,
            layout_data={"blocks": []},
        )
        db_session.add(page)

        # 5. Classification Result
        classification = ClassificationResultModel(
            document_id="doc-prod-001",
            document_type="invoice",
            confidence=0.98,
            classifier_name="sgd_tfidf",
            probabilities={"invoice": 0.98, "receipt": 0.02},
            classified_at=now,
        )
        db_session.add(classification)

        # 6. Extraction Result
        extraction = ExtractionResultModel(
            document_id="doc-prod-001",
            document_type="invoice",
            invoice_number="INV-2026-001",
            vendor="Acme Corp",
            total_amount=500.0,
            extracted_fields={
                "invoice_number": {"value": "INV-2026-001"},
                "vendor": {"value": "Acme Corp"},
                "total_amount": {"value": 500.0},
            },
            extraction_method="hybrid",
            extraction_version="2.0.0",
            extracted_at=now,
        )
        db_session.add(extraction)

        # 7. Validation Result
        validation = ValidationResultModel(
            document_id="doc-prod-001",
            document_type="invoice",
            status="valid",
            rule_results=[{"rule": "total_math", "passed": True}],
            validated_at=now,
        )
        db_session.add(validation)

        # 8. Anomaly Result
        anomaly = AnomalyResultModel(
            document_id="doc-prod-001",
            is_anomaly=False,
            anomaly_score=0.12,
            decision_function_score=0.25,
            features={"invoice_amount": 500.0, "item_count": 2},
            model_version="isolation_forest_v1",
            detected_at=now,
        )
        db_session.add(anomaly)

        # 9. Duplicate Result (needs second document)
        doc2 = Document(
            document_id="doc-prod-002",
            filename="invoice_copy.pdf",
            file_type="pdf",
            file_size=4090,
            file_path="uploads/invoice_copy.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        db_session.add(doc2)

        duplicate = DuplicateResultModel(
            document_id="doc-prod-001",
            matched_document_id="doc-prod-002",
            similarity_score=0.97,
            duplicate_type="near_duplicate",
            detected_at=now,
        )
        db_session.add(duplicate)

        # 10. Document Review (Human-in-the-Loop)
        review = DocumentReviewModel(
            document_id="doc-prod-001",
            reviewer_id="usr-001",
            review_status="approved",
            corrections={"total_amount": 500.0},
            notes="Verified vendor and total against purchase order",
            reviewed_at=now,
        )
        db_session.add(review)

        # 11. Model Metadata
        metadata = ModelMetadataModel(
            name="document_classifier",
            version="v2.1.0",
            model_type="sgd_classifier",
            artifact_path="models/classifier_v2.1.0.joblib",
            parameters={"alpha": 0.0001, "loss": "log_loss"},
            metrics={"accuracy": 0.965, "f1_macro": 0.961},
            is_active=True,
            trained_at=now,
        )
        db_session.add(metadata)

        db_session.commit()

        # Query and verify
        assert db_session.get(UserModel, "usr-001") is not None
        assert db_session.get(Document, "doc-prod-001") is not None
        assert db_session.get(Document, "doc-prod-002") is not None
        assert db_session.scalar(select(DocumentContent).where(DocumentContent.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(DocumentPage).where(DocumentPage.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(ClassificationResultModel).where(ClassificationResultModel.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(ExtractionResultModel).where(ExtractionResultModel.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(ValidationResultModel).where(ValidationResultModel.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(AnomalyResultModel).where(AnomalyResultModel.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(DuplicateResultModel).where(DuplicateResultModel.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(DocumentReviewModel).where(DocumentReviewModel.document_id == "doc-prod-001")) is not None
        assert db_session.scalar(select(ModelMetadataModel).where(ModelMetadataModel.name == "document_classifier")) is not None


# ====================================================
# ORM Relationship Navigation Tests
# ====================================================

class TestORMRelationships:

    def test_bidirectional_relationships(self, db_session):
        now = datetime.now(timezone.utc)

        user = UserModel(
            id="usr-rel-1",
            email="manager@nexora.io",
            hashed_password="hashed_pwd_secret",
            full_name="Review Manager",
        )
        doc = Document(
            document_id="doc-rel-1",
            user=user,
            filename="receipt.png",
            file_type="png",
            file_size=1024,
            file_path="uploads/receipt.png",
            status=DocumentStatus.COMPLETED,
            document_type="receipt",
            created_at=now,
            updated_at=now,
        )
        content = DocumentContent(
            raw_text="Coffee Shop $4.50",
            cleaned_text="coffee shop 4.50",
            extraction_method="tesseract",
            page_count=1,
        )
        doc.content = content

        page = DocumentPage(
            page_number=1,
            raw_text="Coffee Shop",
            cleaned_text="coffee shop",
            extraction_method="tesseract",
            image_path="pages/receipt_p1.png",
            image_width=600,
            image_height=800,
        )
        doc.pages.append(page)

        classification = ClassificationResultModel(
            document_type="receipt",
            confidence=0.99,
            classifier_name="sgd_tfidf",
        )
        doc.classification = classification

        extraction = ExtractionResultModel(
            document_type="receipt",
            vendor="Coffee Shop",
            total_amount=4.50,
            extracted_fields={"total": 4.50},
        )
        doc.extraction = extraction

        validation = ValidationResultModel(
            document_type="receipt",
            status="valid",
            rule_results=[],
        )
        doc.validation = validation

        anomaly = AnomalyResultModel(
            is_anomaly=False,
            anomaly_score=0.05,
            decision_function_score=0.35,
            features={"invoice_amount": 4.50},
            model_version="isolation_forest_v1",
        )
        doc.anomaly = anomaly

        review = DocumentReviewModel(
            reviewer=user,
            review_status="approved",
            notes="Standard expense",
        )
        doc.reviews.append(review)

        db_session.add(user)
        db_session.add(doc)
        db_session.commit()

        # Re-fetch document and assert relationships
        db_doc = db_session.get(Document, "doc-rel-1")
        assert db_doc.user.email == "manager@nexora.io"
        assert db_doc in db_doc.user.documents
        assert db_doc.content.cleaned_text == "coffee shop 4.50"
        assert db_doc.content.document == db_doc
        assert len(db_doc.pages) == 1
        assert db_doc.pages[0].document == db_doc
        assert db_doc.classification.document_type == "receipt"
        assert db_doc.classification.document == db_doc
        assert db_doc.extraction.vendor == "Coffee Shop"
        assert db_doc.extraction.document == db_doc
        assert db_doc.validation.status == "valid"
        assert db_doc.validation.document == db_doc
        assert db_doc.anomaly.is_anomaly is False
        assert db_doc.anomaly.document == db_doc
        assert len(db_doc.reviews) == 1
        assert db_doc.reviews[0].reviewer.email == "manager@nexora.io"
        assert db_doc.reviews[0] in user.reviews


# ====================================================
# Cascading Deletes & Referential Integrity Tests
# ====================================================

class TestCascadingDeletes:

    def test_delete_document_cascades_to_all_children(self, db_session):
        now = datetime.now(timezone.utc)

        user = UserModel(
            id="usr-casc-1",
            email="casc@nexora.io",
            hashed_password="pwd",
        )
        doc1 = Document(
            document_id="doc-casc-main",
            user=user,
            filename="delete_me.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="uploads/delete_me.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        doc2 = Document(
            document_id="doc-casc-matched",
            filename="peer.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="uploads/peer.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([user, doc1, doc2])
        db_session.commit()

        # Add children
        content = DocumentContent(
            document_id="doc-casc-main",
            raw_text="text",
            cleaned_text="text",
            extraction_method="ocr",
        )
        page = DocumentPage(
            document_id="doc-casc-main",
            page_number=1,
            extraction_method="ocr",
            image_path="img.png",
            image_width=100,
            image_height=100,
        )
        classification = ClassificationResultModel(
            document_id="doc-casc-main",
            document_type="invoice",
            confidence=0.9,
        )
        extraction = ExtractionResultModel(
            document_id="doc-casc-main",
            document_type="invoice",
        )
        validation = ValidationResultModel(
            document_id="doc-casc-main",
            document_type="invoice",
            status="valid",
            rule_results=[],
        )
        anomaly = AnomalyResultModel(
            document_id="doc-casc-main",
            is_anomaly=False,
            anomaly_score=0.1,
            decision_function_score=0.2,
            features={},
        )
        duplicate = DuplicateResultModel(
            document_id="doc-casc-main",
            matched_document_id="doc-casc-matched",
            similarity_score=0.95,
            duplicate_type="near_duplicate",
        )
        review = DocumentReviewModel(
            document_id="doc-casc-main",
            reviewer_id="usr-casc-1",
            review_status="pending",
        )

        db_session.add_all([
            content, page, classification, extraction,
            validation, anomaly, duplicate, review,
        ])
        db_session.commit()

        # Delete the main document
        db_session.delete(doc1)
        db_session.commit()

        # Verify child records were deleted
        assert db_session.get(Document, "doc-casc-main") is None
        assert db_session.scalar(select(DocumentContent).where(DocumentContent.document_id == "doc-casc-main")) is None
        assert db_session.scalar(select(DocumentPage).where(DocumentPage.document_id == "doc-casc-main")) is None
        assert db_session.scalar(select(ClassificationResultModel).where(ClassificationResultModel.document_id == "doc-casc-main")) is None
        assert db_session.scalar(select(ExtractionResultModel).where(ExtractionResultModel.document_id == "doc-casc-main")) is None
        assert db_session.scalar(select(ValidationResultModel).where(ValidationResultModel.document_id == "doc-casc-main")) is None
        assert db_session.scalar(select(AnomalyResultModel).where(AnomalyResultModel.document_id == "doc-casc-main")) is None
        assert db_session.scalar(select(DocumentReviewModel).where(DocumentReviewModel.document_id == "doc-casc-main")) is None
        assert db_session.scalar(select(DuplicateResultModel).where(DuplicateResultModel.document_id == "doc-casc-main")) is None

        # Verify user and matched peer document still exist
        assert db_session.get(UserModel, "usr-casc-1") is not None
        assert db_session.get(Document, "doc-casc-matched") is not None

    def test_delete_user_sets_foreign_keys_to_null(self, db_session):
        now = datetime.now(timezone.utc)

        user = UserModel(
            id="usr-del-1",
            email="departing_user@nexora.io",
            hashed_password="secret_password",
        )
        doc = Document(
            document_id="doc-survives-user",
            user=user,
            filename="report.pdf",
            file_type="pdf",
            file_size=2048,
            file_path="uploads/report.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        review = DocumentReviewModel(
            document_id="doc-survives-user",
            reviewer=user,
            review_status="approved",
        )
        db_session.add_all([user, doc, review])
        db_session.commit()

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Document and review must still exist, with user_id/reviewer_id set to None
        db_doc = db_session.get(Document, "doc-survives-user")
        assert db_doc is not None
        assert db_doc.user_id is None
        assert db_doc.user is None

        db_review = db_session.scalar(select(DocumentReviewModel).where(DocumentReviewModel.document_id == "doc-survives-user"))
        assert db_review is not None
        assert db_review.reviewer_id is None
        assert db_review.reviewer is None


# ====================================================
# Unique Constraints Tests
# ====================================================

class TestUniqueConstraints:

    def test_user_email_must_be_unique(self, db_session):
        u1 = UserModel(
            id="usr-uq-1",
            email="duplicate@nexora.io",
            hashed_password="pwd1",
        )
        u2 = UserModel(
            id="usr-uq-2",
            email="duplicate@nexora.io",
            hashed_password="pwd2",
        )
        db_session.add(u1)
        db_session.commit()

        db_session.add(u2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_model_metadata_name_and_version_must_be_unique(self, db_session):
        m1 = ModelMetadataModel(
            name="isolation_forest",
            version="v1.0.0",
            model_type="anomaly_detection",
            artifact_path="models/iso_v1.joblib",
        )
        m2 = ModelMetadataModel(
            name="isolation_forest",
            version="v1.0.0",
            model_type="anomaly_detection",
            artifact_path="models/iso_v1_other.joblib",
        )
        db_session.add(m1)
        db_session.commit()

        db_session.add(m2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_duplicate_result_pair_must_be_unique(self, db_session):
        now = datetime.now(timezone.utc)
        d1 = Document(
            document_id="doc-dup-a",
            filename="a.pdf",
            file_type="pdf",
            file_size=10,
            file_path="a.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        d2 = Document(
            document_id="doc-dup-b",
            filename="b.pdf",
            file_type="pdf",
            file_size=10,
            file_path="b.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([d1, d2])
        db_session.commit()

        r1 = DuplicateResultModel(
            document_id="doc-dup-a",
            matched_document_id="doc-dup-b",
            similarity_score=0.98,
            duplicate_type="exact_duplicate",
        )
        r2 = DuplicateResultModel(
            document_id="doc-dup-a",
            matched_document_id="doc-dup-b",
            similarity_score=0.99,
            duplicate_type="exact_duplicate",
        )
        db_session.add(r1)
        db_session.commit()

        db_session.add(r2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


# ====================================================
# Search Queries & Extraction Repository Tests
# ====================================================

class TestExtractionRepositoryAndIndexes:

    def test_extraction_repository_auto_indexes_fields(self, db_session):
        now = datetime.now(timezone.utc)
        doc = Document(
            document_id="doc-repo-test",
            filename="invoice.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="uploads/invoice.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        db_session.add(doc)
        db_session.commit()

        repo = ExtractionResultRepository(db_session)
        fields = {
            "invoice_number": {"value": "INV-GLOBAL-999"},
            "vendor": {"value": "Global Tech Logistics"},
            "total_amount": {"value": "$1,450.75"},
        }
        saved = repo.save(
            document_id="doc-repo-test",
            document_type="invoice",
            extracted_fields=fields,
            extraction_method="regex_heuristic",
            extraction_version="1.0.0",
        )

        assert saved.invoice_number == "INV-GLOBAL-999"
        assert saved.vendor == "Global Tech Logistics"
        assert saved.total_amount == 1450.75

        # Search by invoice number
        matches = repo.search_by_invoice_number("INV-GLOBAL-999")
        assert len(matches) == 1
        assert matches[0].document_id == "doc-repo-test"

        # Search by vendor
        vendor_matches = repo.search_by_vendor("Global Tech Logistics")
        assert len(vendor_matches) == 1
        assert vendor_matches[0].document_id == "doc-repo-test"

    def test_query_document_by_type_and_status(self, db_session):
        now = datetime.now(timezone.utc)
        docs = [
            Document(
                document_id="doc-idx-1",
                filename="inv1.pdf",
                file_type="pdf",
                file_size=10,
                file_path="p",
                document_type="invoice",
                status=DocumentStatus.COMPLETED,
                created_at=now,
                updated_at=now,
            ),
            Document(
                document_id="doc-idx-2",
                filename="inv2.pdf",
                file_type="pdf",
                file_size=10,
                file_path="p",
                document_type="invoice",
                status=DocumentStatus.PROCESSING,
                created_at=now,
                updated_at=now,
            ),
            Document(
                document_id="doc-idx-3",
                filename="rec1.pdf",
                file_type="pdf",
                file_size=10,
                file_path="p",
                document_type="receipt",
                status=DocumentStatus.COMPLETED,
                created_at=now,
                updated_at=now,
            ),
        ]
        db_session.add_all(docs)
        db_session.commit()

        # Query composite (document_type, status)
        stmt = select(Document).where(
            Document.document_type == "invoice",
            Document.status == DocumentStatus.COMPLETED,
        )
        results = list(db_session.scalars(stmt).all())
        assert len(results) == 1
        assert results[0].document_id == "doc-idx-1"
