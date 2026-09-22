"""
Batch Processing Service — Multi-Document Upload Tracking.

Provides an in-memory, thread-safe tracker for batch document
uploads. Each batch maintains per-item status so the frontend
can poll for progress.
"""

import logging
import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


logger = logging.getLogger(__name__)


class BatchItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class BatchItem:
    """Status record for a single document within a batch."""

    def __init__(self, document_id: str, filename: str):
        self.document_id = document_id
        self.filename = filename
        self.status = BatchItemStatus.PENDING
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "status": self.status.value,
            "error": self.error,
            "started_at": (
                self.started_at.isoformat()
                if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat()
                if self.completed_at else None
            ),
        }


class Batch:
    """Aggregate tracker for a batch of documents."""

    def __init__(self, batch_id: str):
        self.batch_id = batch_id
        self.items: dict[str, BatchItem] = {}
        self.created_at = datetime.now(timezone.utc)

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def pending_count(self) -> int:
        return sum(
            1 for i in self.items.values()
            if i.status == BatchItemStatus.PENDING
        )

    @property
    def processing_count(self) -> int:
        return sum(
            1 for i in self.items.values()
            if i.status == BatchItemStatus.PROCESSING
        )

    @property
    def completed_count(self) -> int:
        return sum(
            1 for i in self.items.values()
            if i.status == BatchItemStatus.COMPLETED
        )

    @property
    def failed_count(self) -> int:
        return sum(
            1 for i in self.items.values()
            if i.status == BatchItemStatus.FAILED
        )

    @property
    def overall_status(self) -> BatchStatus:
        if self.pending_count == self.total:
            return BatchStatus.PENDING
        if self.processing_count > 0 or self.pending_count > 0:
            return BatchStatus.PROCESSING
        if self.failed_count == self.total:
            return BatchStatus.FAILED
        if self.failed_count > 0:
            return BatchStatus.PARTIAL
        return BatchStatus.COMPLETED

    @property
    def progress_percent(self) -> float:
        if self.total == 0:
            return 100.0
        done = self.completed_count + self.failed_count
        return round((done / self.total) * 100, 1)

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "status": self.overall_status.value,
            "total": self.total,
            "pending": self.pending_count,
            "processing": self.processing_count,
            "completed": self.completed_count,
            "failed": self.failed_count,
            "progress_percent": self.progress_percent,
            "created_at": self.created_at.isoformat(),
            "items": [
                item.to_dict()
                for item in self.items.values()
            ],
        }


class BatchService:
    """
    Thread-safe in-memory batch tracker.

    Designed for single-process deployments (uvicorn
    with default workers). For multi-worker setups,
    replace with Redis or database-backed storage.
    """

    _instance: Optional["BatchService"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._batches: dict[str, Batch] = {}
                cls._instance._batch_lock = threading.Lock()
            return cls._instance

    def create_batch(
        self,
        items: list[dict],
    ) -> Batch:
        """
        Create a new batch.

        Args:
            items: List of dicts with 'document_id' and 'filename'.

        Returns:
            Batch object.
        """
        batch_id = str(uuid4())
        batch = Batch(batch_id)

        for item in items:
            doc_id = item["document_id"]
            filename = item.get("filename", "unknown")
            batch.items[doc_id] = BatchItem(
                document_id=doc_id,
                filename=filename,
            )

        with self._batch_lock:
            self._batches[batch_id] = batch

        logger.info(
            "Created batch %s with %d documents",
            batch_id,
            len(items),
        )

        return batch

    def update_item_status(
        self,
        batch_id: str,
        document_id: str,
        status: BatchItemStatus,
        error: Optional[str] = None,
    ):
        """Update processing status of a single item in a batch."""
        with self._batch_lock:
            batch = self._batches.get(batch_id)
            if not batch:
                return
            item = batch.items.get(document_id)
            if not item:
                return

            item.status = status
            now = datetime.now(timezone.utc)

            if status == BatchItemStatus.PROCESSING:
                item.started_at = now
            elif status in (
                BatchItemStatus.COMPLETED,
                BatchItemStatus.FAILED,
            ):
                item.completed_at = now

            if error:
                item.error = error

        logger.debug(
            "Batch %s — doc %s → %s",
            batch_id,
            document_id,
            status.value,
        )

    def get_batch(self, batch_id: str) -> Optional[Batch]:
        """Get batch status."""
        with self._batch_lock:
            return self._batches.get(batch_id)

    def get_batch_status(self, batch_id: str) -> Optional[dict]:
        """Get batch status as a serializable dict."""
        batch = self.get_batch(batch_id)
        if batch is None:
            return None
        return batch.to_dict()

    def cleanup_old_batches(self, max_age_hours: int = 24):
        """Remove batches older than max_age_hours."""
        now = datetime.now(timezone.utc)
        with self._batch_lock:
            stale = [
                bid for bid, b in self._batches.items()
                if (now - b.created_at).total_seconds()
                > max_age_hours * 3600
            ]
            for bid in stale:
                del self._batches[bid]

        if stale:
            logger.info(
                "Cleaned up %d stale batches", len(stale)
            )


def get_batch_service() -> BatchService:
    """Get the singleton BatchService instance."""
    return BatchService()
