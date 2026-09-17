"""
Extraction service.

Orchestrates document extraction by:
1. Looking up the right extractor via the registry
2. Running extraction on the document text
3. Persisting the result via the repository
"""

import logging
from typing import Optional

from app.ml.extraction.base import (
    ExtractionResult,
)
from app.ml.extraction.registry import (
    ExtractionStrategyRegistry,
)
from app.services.extraction_result_repository import (
    ExtractionResultRepository,
)


logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting structured fields
    from classified documents.

    Uses the strategy pattern: the registry maps
    document_type → extractor. If no extractor is
    registered for a type, extraction is skipped.
    """

    def __init__(
        self,
        registry: ExtractionStrategyRegistry,
        repository: ExtractionResultRepository,
    ):

        self.registry = registry
        self.repository = repository

    def extract_document(
        self,
        document_id: str,
        document_type: str,
        cleaned_text: str,
        pages: list[dict] | None = None,
    ) -> Optional[ExtractionResult]:
        """Extract structured fields from a
        document.

        Args:
            document_id: The document ID.
            document_type: Classified type (e.g.
                           "invoice").
            cleaned_text: The cleaned, concatenated
                          text.
            pages: Optional page-level data.

        Returns:
            ExtractionResult or None if no extractor
            is available for this document type.
        """

        extractor = self.registry.get(
            document_type
        )

        if extractor is None:

            logger.debug(
                "No extractor registered for "
                "document type '%s', skipping "
                "extraction for %s",
                document_type,
                document_id,
            )

            return None

        result = extractor.extract(
            cleaned_text, pages
        )

        # Persist to database
        result_dict = result.to_dict()

        self.repository.save(
            document_id=document_id,
            document_type=result.document_type,
            extracted_fields=result_dict["fields"],
            extraction_method=(
                result.extraction_method
            ),
            extraction_version=result.version,
        )

        logger.info(
            "Extraction completed for document "
            "%s (type=%s, method=%s, fields=%d)",
            document_id,
            result.document_type,
            result.extraction_method,
            len(result.fields),
        )

        return result
