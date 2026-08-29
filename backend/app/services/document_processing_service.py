import logging

from app.models.document import DocumentStatus

from app.processing.pipeline import (
    DocumentProcessingPipeline
)

from app.services.document_repository import (
    DocumentRepository
)


logger = logging.getLogger(__name__)


class DocumentProcessingService:

    def __init__(
        self,
        repository: DocumentRepository,
        pipeline: DocumentProcessingPipeline
    ):

        self.repository = repository

        self.pipeline = pipeline

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

            self.pipeline.process(
                document
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