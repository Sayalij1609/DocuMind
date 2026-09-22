"""
Tests for Phase 13 services:
  - BatchService
  - OCRCorrectionService
  - ComparisonService (unit-level)
  - ConfidenceService (unit-level)
  - ReportService (PDF generation)
"""

import pytest
import threading
from unittest.mock import MagicMock, patch

# ==========================================
# 1. BatchService Tests
# ==========================================

from app.services.batch_service import (
    BatchService,
    BatchItemStatus,
    BatchStatus,
    Batch,
    BatchItem,
)


class TestBatchService:
    """Tests for multi-document batch processing tracker."""

    def setup_method(self):
        """Reset singleton for clean tests."""
        BatchService._instance = None
        self.svc = BatchService()

    def test_singleton(self):
        """BatchService should be a singleton."""
        svc2 = BatchService()
        assert self.svc is svc2

    def test_create_batch(self):
        """Should create a batch with items."""
        items = [
            {"document_id": "doc-1", "filename": "a.pdf"},
            {"document_id": "doc-2", "filename": "b.pdf"},
        ]
        batch = self.svc.create_batch(items)

        assert batch.total == 2
        assert batch.pending_count == 2
        assert batch.completed_count == 0
        assert batch.overall_status == BatchStatus.PENDING

    def test_update_item_status(self):
        """Should update individual item status."""
        items = [
            {"document_id": "doc-1", "filename": "a.pdf"},
        ]
        batch = self.svc.create_batch(items)

        self.svc.update_item_status(
            batch.batch_id, "doc-1",
            BatchItemStatus.PROCESSING,
        )
        assert batch.items["doc-1"].status == BatchItemStatus.PROCESSING
        assert batch.items["doc-1"].started_at is not None
        assert batch.overall_status == BatchStatus.PROCESSING

    def test_batch_completion(self):
        """Batch should report COMPLETED when all items done."""
        items = [
            {"document_id": "doc-1", "filename": "a.pdf"},
            {"document_id": "doc-2", "filename": "b.pdf"},
        ]
        batch = self.svc.create_batch(items)

        self.svc.update_item_status(
            batch.batch_id, "doc-1",
            BatchItemStatus.COMPLETED,
        )
        self.svc.update_item_status(
            batch.batch_id, "doc-2",
            BatchItemStatus.COMPLETED,
        )

        assert batch.overall_status == BatchStatus.COMPLETED
        assert batch.progress_percent == 100.0

    def test_batch_partial_failure(self):
        """Batch should report PARTIAL when some items fail."""
        items = [
            {"document_id": "doc-1", "filename": "a.pdf"},
            {"document_id": "doc-2", "filename": "b.pdf"},
        ]
        batch = self.svc.create_batch(items)

        self.svc.update_item_status(
            batch.batch_id, "doc-1",
            BatchItemStatus.COMPLETED,
        )
        self.svc.update_item_status(
            batch.batch_id, "doc-2",
            BatchItemStatus.FAILED,
            error="OCR error",
        )

        assert batch.overall_status == BatchStatus.PARTIAL
        assert batch.failed_count == 1
        assert batch.items["doc-2"].error == "OCR error"

    def test_get_batch_status_dict(self):
        """Should return serializable dict."""
        items = [
            {"document_id": "doc-1", "filename": "a.pdf"},
        ]
        batch = self.svc.create_batch(items)
        status = self.svc.get_batch_status(batch.batch_id)

        assert isinstance(status, dict)
        assert status["batch_id"] == batch.batch_id
        assert status["total"] == 1
        assert len(status["items"]) == 1

    def test_nonexistent_batch(self):
        """Should return None for unknown batch."""
        assert self.svc.get_batch_status("fake") is None

    def test_thread_safety(self):
        """Concurrent updates should not corrupt state."""
        items = [
            {"document_id": f"doc-{i}", "filename": f"{i}.pdf"}
            for i in range(10)
        ]
        batch = self.svc.create_batch(items)

        def update(doc_id):
            self.svc.update_item_status(
                batch.batch_id, doc_id,
                BatchItemStatus.COMPLETED,
            )

        threads = [
            threading.Thread(target=update, args=(f"doc-{i}",))
            for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert batch.completed_count == 10
        assert batch.overall_status == BatchStatus.COMPLETED


# ==========================================
# 2. OCRCorrectionService Tests
# ==========================================

from app.services.ocr_correction_service import (
    OCRCorrectionService,
)


class TestOCRCorrectionService:
    """Tests for OCR post-processing correction."""

    def test_empty_text(self):
        """Empty text should return empty."""
        svc = OCRCorrectionService(api_key=None)
        assert svc.correct_text("") == ""
        assert svc.correct_text(None) == ""

    def test_short_text_passthrough(self):
        """Short text under 20 chars should pass through."""
        svc = OCRCorrectionService(api_key=None)
        result = svc.correct_text("Hello World")
        assert result == "Hello World"

    def test_rule_based_rn_correction(self):
        """Should fix rn→m in common words."""
        svc = OCRCorrectionService(api_key=None)
        text = "The governrnent issued a payrnent docurnent"
        result = svc.correct_text(text)
        assert "government" in result
        assert "payment" in result
        assert "document" in result

    def test_rule_based_total1_correction(self):
        """Should fix Tota1 → Total."""
        svc = OCRCorrectionService(api_key=None)
        text = "Tota1 amount is $1,234.56 on the Invo1ce"
        result = svc.correct_text(text)
        assert "Total" in result

    def test_excessive_whitespace(self):
        """Should reduce excessive spaces."""
        svc = OCRCorrectionService(api_key=None)
        text = "Invoice     Number     12345     is ready for review"
        result = svc.correct_text(text)
        assert "     " not in result

    def test_garbled_punctuation(self):
        """Should clean repeated punctuation."""
        svc = OCRCorrectionService(api_key=None)
        text = "Amount due,,, is $500.00....... please pay"
        result = svc.correct_text(text)
        assert ",,," not in result
        assert "......." not in result


# ==========================================
# 3. BatchItem / Batch Model Tests
# ==========================================


class TestBatchModels:
    """Tests for batch data models."""

    def test_batch_item_to_dict(self):
        item = BatchItem("doc-1", "test.pdf")
        d = item.to_dict()
        assert d["document_id"] == "doc-1"
        assert d["filename"] == "test.pdf"
        assert d["status"] == "pending"

    def test_batch_progress_empty(self):
        batch = Batch("test-batch")
        assert batch.progress_percent == 100.0

    def test_batch_to_dict(self):
        batch = Batch("test-batch")
        batch.items["doc-1"] = BatchItem("doc-1", "a.pdf")
        d = batch.to_dict()
        assert d["batch_id"] == "test-batch"
        assert d["total"] == 1
        assert len(d["items"]) == 1
