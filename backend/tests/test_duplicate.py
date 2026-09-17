"""
Unit tests for Phase 8 — Duplicate Document Detection.

Tests:
- TF-IDF similarity engine
- Content hash (exact duplicate detection)
- Identical documents
- Highly similar documents
- Unrelated documents
- Empty documents
- Threshold boundary
- DuplicateMatch / DuplicateCheckResult
- Batch similarity
"""

import pytest

from app.dedup.base import (
    DuplicateMatch,
    DuplicateCheckResult,
    DuplicateType,
)
from app.dedup.tfidf_engine import (
    TfidfSimilarityEngine,
    compute_content_hash,
)


# ====================================================
# Content hash tests
# ====================================================

class TestContentHash:

    def test_identical_texts(self):
        h1 = compute_content_hash("Hello World")
        h2 = compute_content_hash("Hello World")
        assert h1 == h2

    def test_whitespace_normalized(self):
        h1 = compute_content_hash("Hello  World")
        h2 = compute_content_hash("Hello World")
        assert h1 == h2

    def test_tabs_and_newlines(self):
        h1 = compute_content_hash("Hello\tWorld\n")
        h2 = compute_content_hash("Hello World")
        assert h1 == h2

    def test_case_insensitive(self):
        h1 = compute_content_hash("HELLO WORLD")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_different_texts(self):
        h1 = compute_content_hash("Invoice 001")
        h2 = compute_content_hash("Purchase Order 001")
        assert h1 != h2

    def test_empty_text(self):
        h1 = compute_content_hash("")
        h2 = compute_content_hash("")
        assert h1 == h2

    def test_returns_hex_string(self):
        h = compute_content_hash("test")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex


# ====================================================
# TF-IDF similarity engine tests
# ====================================================

class TestTfidfSimilarityEngine:

    def setup_method(self):
        self.engine = TfidfSimilarityEngine()

    def test_identical_documents(self):
        text = (
            "Invoice Number INV-001 "
            "Date September 1 2026 "
            "Total Amount 100890"
        )
        score = self.engine.compute_similarity(
            text, text
        )
        assert score >= 0.99

    def test_highly_similar_documents(self):
        """Same invoice, different number/date."""
        text_a = (
            "Invoice Number INV-001 "
            "Date September 1 2026 "
            "Vendor Acme Corp "
            "Subtotal 85500 Tax 15390 "
            "Total 100890"
        )
        text_b = (
            "Invoice Number INV-002 "
            "Date September 5 2026 "
            "Vendor Acme Corp "
            "Subtotal 85500 Tax 15390 "
            "Total 100890"
        )
        score = self.engine.compute_similarity(
            text_a, text_b
        )
        # High but not perfect
        assert score >= 0.7
        assert score < 1.0

    def test_unrelated_documents(self):
        text_a = (
            "Invoice Number INV-001 "
            "Vendor Acme Corp "
            "Total 100890"
        )
        text_b = (
            "The quick brown fox jumps over "
            "the lazy dog on a sunny day "
            "in the park near the river"
        )
        score = self.engine.compute_similarity(
            text_a, text_b
        )
        assert score < 0.3

    def test_empty_first_document(self):
        score = self.engine.compute_similarity(
            "", "Some text here"
        )
        assert score == 0.0

    def test_empty_second_document(self):
        score = self.engine.compute_similarity(
            "Some text here", ""
        )
        assert score == 0.0

    def test_both_empty(self):
        score = self.engine.compute_similarity(
            "", ""
        )
        assert score == 0.0

    def test_whitespace_only(self):
        score = self.engine.compute_similarity(
            "   ", "Some text"
        )
        assert score == 0.0

    def test_score_range(self):
        """Score should always be in [0.0, 1.0]."""
        score = self.engine.compute_similarity(
            "Invoice total 100",
            "Invoice total 200",
        )
        assert 0.0 <= score <= 1.0

    def test_same_words_different_order(self):
        text_a = "invoice total amount due"
        text_b = "amount due total invoice"
        score = self.engine.compute_similarity(
            text_a, text_b
        )
        # Same unigrams → high similarity
        assert score >= 0.5


# ====================================================
# Batch similarity tests
# ====================================================

class TestBatchSimilarity:

    def setup_method(self):
        self.engine = TfidfSimilarityEngine()

    def test_batch_returns_correct_count(self):
        query = "Invoice Number INV-001"
        candidates = [
            "Invoice Number INV-001",
            "Purchase Order PO-100",
            "Invoice Number INV-002",
        ]
        scores = (
            self.engine
            .compute_similarities_batch(
                query, candidates
            )
        )
        assert len(scores) == 3

    def test_batch_identical_first(self):
        query = "Invoice total 100890"
        candidates = [
            "Invoice total 100890",
            "Something completely different",
        ]
        scores = (
            self.engine
            .compute_similarities_batch(
                query, candidates
            )
        )
        assert scores[0] >= 0.99
        assert scores[1] < scores[0]

    def test_batch_empty_query(self):
        scores = (
            self.engine
            .compute_similarities_batch(
                "", ["text1", "text2"]
            )
        )
        assert scores == [0.0, 0.0]

    def test_batch_empty_candidates(self):
        scores = (
            self.engine
            .compute_similarities_batch(
                "query text", []
            )
        )
        assert scores == []

    def test_batch_consistency_with_pairwise(self):
        """Batch scores should be similar to
        individual pairwise comparisons."""
        query = "Invoice INV-001 total 100890"
        candidates = [
            "Invoice INV-001 total 100890",
            "Purchase Order PO-001 total 50000",
        ]

        batch_scores = (
            self.engine
            .compute_similarities_batch(
                query, candidates
            )
        )

        # Note: batch and pairwise may differ
        # slightly due to shared vocabulary,
        # but the ranking should be the same
        assert batch_scores[0] > batch_scores[1]


# ====================================================
# DuplicateMatch tests
# ====================================================

class TestDuplicateMatch:

    def test_to_dict(self):
        match = DuplicateMatch(
            document_id="doc-1",
            matched_document_id="doc-2",
            similarity_score=0.943,
            duplicate_type=DuplicateType.NEAR,
        )
        d = match.to_dict()
        assert d["document_id"] == "doc-1"
        assert d["matched_document_id"] == "doc-2"
        assert d["similarity_score"] == 0.943
        assert d["duplicate_type"] == "near"

    def test_exact_type(self):
        match = DuplicateMatch(
            document_id="a",
            matched_document_id="b",
            similarity_score=1.0,
            duplicate_type=DuplicateType.EXACT,
        )
        assert match.duplicate_type == (
            DuplicateType.EXACT
        )

    def test_score_rounding(self):
        match = DuplicateMatch(
            document_id="a",
            matched_document_id="b",
            similarity_score=0.94312345,
            duplicate_type=DuplicateType.NEAR,
        )
        d = match.to_dict()
        assert d["similarity_score"] == 0.9431


# ====================================================
# DuplicateCheckResult tests
# ====================================================

class TestDuplicateCheckResult:

    def test_no_matches(self):
        result = DuplicateCheckResult(
            document_id="doc-1",
            matches=[],
        )
        assert not result.has_duplicates
        assert result.exact_matches == []
        assert result.near_matches == []

    def test_with_matches(self):
        exact = DuplicateMatch(
            document_id="doc-1",
            matched_document_id="doc-2",
            similarity_score=1.0,
            duplicate_type=DuplicateType.EXACT,
        )
        near = DuplicateMatch(
            document_id="doc-1",
            matched_document_id="doc-3",
            similarity_score=0.88,
            duplicate_type=DuplicateType.NEAR,
        )
        result = DuplicateCheckResult(
            document_id="doc-1",
            matches=[exact, near],
            candidates_checked=10,
        )
        assert result.has_duplicates
        assert len(result.exact_matches) == 1
        assert len(result.near_matches) == 1
        assert result.candidates_checked == 10

    def test_multiple_near(self):
        matches = [
            DuplicateMatch(
                document_id="doc-1",
                matched_document_id=f"doc-{i}",
                similarity_score=0.9 - i * 0.01,
                duplicate_type=DuplicateType.NEAR,
            )
            for i in range(5)
        ]
        result = DuplicateCheckResult(
            document_id="doc-1",
            matches=matches,
        )
        assert len(result.near_matches) == 5
        assert len(result.exact_matches) == 0


# ====================================================
# Threshold boundary tests
# ====================================================

class TestThresholdBoundary:

    def test_exact_at_boundary(self):
        """Score of exactly 0.99 should be EXACT
        with default threshold."""
        engine = TfidfSimilarityEngine()
        # Use almost identical texts
        text = (
            "Invoice Number INV-001 "
            "Total Amount 100890 "
            "Vendor Acme Corporation Ltd "
            "Date September 2026 "
            "Due Date October 2026"
        )
        score = engine.compute_similarity(
            text, text
        )
        assert score >= 0.99

    def test_near_below_exact(self):
        """Two similar but not identical texts
        should be NEAR duplicate, not EXACT."""
        engine = TfidfSimilarityEngine()
        text_a = (
            "Invoice Number INV-001 "
            "Total Amount 100890 "
            "Vendor Acme Corporation"
        )
        text_b = (
            "Invoice Number INV-999 "
            "Total Amount 100890 "
            "Vendor Acme Corporation"
        )
        score = engine.compute_similarity(
            text_a, text_b
        )
        # Similar but not exact
        assert 0.5 < score < 1.0


# ====================================================
# DuplicateType enum
# ====================================================

class TestDuplicateType:

    def test_exact_value(self):
        assert DuplicateType.EXACT.value == "exact"

    def test_near_value(self):
        assert DuplicateType.NEAR.value == "near"

    def test_string_enum(self):
        assert isinstance(
            DuplicateType.EXACT, str
        )


# ====================================================
# Repository & Service Tests (In-Memory SQLite)
# ====================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.models.document import Document, DocumentStatus
from app.models.document_content import DocumentContent
from app.models.duplicate_result import DuplicateResultModel
from app.services.duplicate_result_repository import DuplicateResultRepository
from app.dedup.service import DuplicateDetectionService
from datetime import datetime, timezone


@pytest.fixture
def db_session():
    """In-memory SQLite session with all tables created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestDuplicateResultRepository:

    def test_save_matches_and_retrieve(self, db_session):
        # Create test documents
        now = datetime.now(timezone.utc)
        doc1 = Document(
            document_id="doc-1",
            filename="invoice1.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="uploads/invoice1.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        doc2 = Document(
            document_id="doc-2",
            filename="invoice2.pdf",
            file_type="pdf",
            file_size=1024,
            file_path="uploads/invoice2.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([doc1, doc2])
        db_session.commit()

        repo = DuplicateResultRepository(db_session)
        matches = [
            {
                "document_id": "doc-1",
                "matched_document_id": "doc-2",
                "similarity_score": 0.95,
                "duplicate_type": "near",
                "detected_at": now,
            }
        ]
        saved = repo.save_matches(matches)
        assert len(saved) == 1
        assert saved[0].similarity_score == 0.95

        # Query by doc-1
        results_1 = repo.get_by_document_id("doc-1")
        assert len(results_1) == 1
        assert results_1[0].matched_document_id == "doc-2"

        # Query bidirectional (by doc-2)
        results_2 = repo.get_by_document_id("doc-2")
        assert len(results_2) == 1
        assert results_2[0].document_id == "doc-1"

    def test_upsert_updates_higher_score(self, db_session):
        now = datetime.now(timezone.utc)
        doc1 = Document(
            document_id="doc-A",
            filename="a.pdf",
            file_type="pdf",
            file_size=100,
            file_path="uploads/a.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        doc2 = Document(
            document_id="doc-B",
            filename="b.pdf",
            file_type="pdf",
            file_size=100,
            file_path="uploads/b.pdf",
            status=DocumentStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )
        db_session.add_all([doc1, doc2])
        db_session.commit()

        repo = DuplicateResultRepository(db_session)
        # Initial save with 0.88
        repo.save_matches([
            {
                "document_id": "doc-A",
                "matched_document_id": "doc-B",
                "similarity_score": 0.88,
                "duplicate_type": "near",
                "detected_at": now,
            }
        ])

        # Second save with higher score 0.96
        repo.save_matches([
            {
                "document_id": "doc-A",
                "matched_document_id": "doc-B",
                "similarity_score": 0.96,
                "duplicate_type": "near",
                "detected_at": now,
            }
        ])

        results = repo.get_by_document_id("doc-A")
        assert len(results) == 1
        assert results[0].similarity_score == 0.96


class TestDuplicateDetectionServiceIntegration:

    def test_detects_exact_and_near_duplicates(self, db_session):
        now = datetime.now(timezone.utc)

        # Candidate 1: Exact duplicate content
        d1 = Document(
            document_id="cand-1",
            filename="cand1.pdf",
            file_type="pdf",
            file_size=500,
            file_path="uploads/cand1.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        c1 = DocumentContent(
            document_id="cand-1",
            raw_text="Tax Invoice Acme Corp Total 1000",
            cleaned_text="Tax Invoice Acme Corp Total 1000",
            extraction_method="tesseract",
        )

        # Candidate 2: Near duplicate content
        d2 = Document(
            document_id="cand-2",
            filename="cand2.pdf",
            file_type="pdf",
            file_size=500,
            file_path="uploads/cand2.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        c2 = DocumentContent(
            document_id="cand-2",
            raw_text="Tax Invoice Acme Corp Total 1050 Different PO",
            cleaned_text="Tax Invoice Acme Corp Total 1050 Different PO",
            extraction_method="tesseract",
        )

        # Candidate 3: Unrelated content
        d3 = Document(
            document_id="cand-3",
            filename="cand3.pdf",
            file_type="pdf",
            file_size=500,
            file_path="uploads/cand3.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        c3 = DocumentContent(
            document_id="cand-3",
            raw_text="Medical Report Patient John Doe Blood Test Normal",
            cleaned_text="Medical Report Patient John Doe Blood Test Normal",
            extraction_method="tesseract",
        )

        # Candidate 4: Different document type (should be filtered out)
        d4 = Document(
            document_id="cand-4",
            filename="cand4.pdf",
            file_type="pdf",
            file_size=500,
            file_path="uploads/cand4.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="resume",
            created_at=now,
            updated_at=now,
        )
        c4 = DocumentContent(
            document_id="cand-4",
            raw_text="Tax Invoice Acme Corp Total 1000",
            cleaned_text="Tax Invoice Acme Corp Total 1000",
            extraction_method="tesseract",
        )

        # Target document to check
        target = Document(
            document_id="target-doc",
            filename="target.pdf",
            file_type="pdf",
            file_size=500,
            file_path="uploads/target.pdf",
            status=DocumentStatus.COMPLETED,
            document_type="invoice",
            created_at=now,
            updated_at=now,
        )
        target_content = DocumentContent(
            document_id="target-doc",
            raw_text="Tax Invoice Acme Corp Total 1000",
            cleaned_text="Tax Invoice Acme Corp Total 1000",
            extraction_method="tesseract",
        )

        db_session.add_all([
            d1, c1, d2, c2, d3, c3, d4, c4, target, target_content
        ])
        db_session.commit()

        service = DuplicateDetectionService(
            session=db_session,
            near_threshold=0.50,
            exact_threshold=0.99,
        )

        result = service.check_document("target-doc")

        assert result.has_duplicates is True
        # cand-1 is exact
        assert any(
            m.matched_document_id == "cand-1"
            and m.duplicate_type == DuplicateType.EXACT
            for m in result.matches
        )
        # cand-4 was excluded by document_type filter
        assert not any(
            m.matched_document_id == "cand-4"
            for m in result.matches
        )
        # cand-3 (unrelated) score should be low or not matched
        assert not any(
            m.matched_document_id == "cand-3"
            and m.duplicate_type == DuplicateType.EXACT
            for m in result.matches
        )

