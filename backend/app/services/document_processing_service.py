import logging
from typing import Optional

from app.models.document import DocumentStatus

from app.processing.pipeline import (
    DocumentProcessingPipeline
)

from app.services.classification_service import (
    ClassificationService
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
        ] = None
    ):

        self.repository = repository

        self.pipeline = pipeline

        self.classification_service = (
            classification_service
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

            self._classify_document(
                document_id,
                content.cleaned_text
            )

            self.repository.update_status(
                document_id,
                DocumentStatus.COMPLETED
            )

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
        """

        if self.classification_service is None:

            logger.debug(
                "No classification service "
                "configured, skipping."
            )

            return

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

        except Exception:

            logger.exception(
                "Classification failed for "
                "document %s (non-blocking)",
                document_id
            )