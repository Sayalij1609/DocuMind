"""
Classification service.

Orchestrates document classification by combining
the ML predictor with the document repository.
"""

import logging

from app.ml.classification.predictor import (
    ClassificationResult,
    DocumentClassifier,
)

from app.services.document_repository import (
    DocumentRepository,
)


logger = logging.getLogger(__name__)


class ClassificationService:
    """
    Service for classifying documents.

    Uses the DocumentClassifier (ML predictor)
    and persists results via DocumentRepository.
    """

    def __init__(
        self,
        classifier: DocumentClassifier,
        repository: DocumentRepository
    ):

        self.classifier = classifier
        self.repository = repository

    def classify_document(
        self,
        document_id: str,
        document_text: str
    ) -> ClassificationResult:
        """
        Classify a document and store the result.

        Args:
            document_id: ID of the document.
            document_text: Combined cleaned text
                           from all pages.

        Returns:
            ClassificationResult with document_type
            and confidence.
        """

        result = self.classifier.predict(
            document_text
        )

        logger.info(
            "Document %s classified as '%s' "
            "(confidence: %.4f)",
            document_id,
            result.document_type,
            result.confidence
        )

        self.repository.update_classification(
            document_id=document_id,
            document_type=result.document_type,
            confidence=result.confidence
        )

        return result
