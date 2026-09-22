"""
Document Comparison Service.

Compares two documents across:
  - Document type
  - Extracted fields (field-by-field diff)
  - Textual similarity (TF-IDF cosine)
  - Validation status
  - Key values (totals, dates, vendor)
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.comparison import (
    ComparisonResponse,
    FieldDiff,
)
from app.services.document_repository import (
    DocumentRepository,
)
from app.services.extraction_result_repository import (
    ExtractionResultRepository,
)
from app.services.validation_result_repository import (
    ValidationResultRepository,
)
from app.services.document_content_repository import (
    DocumentContentRepository,
)

logger = logging.getLogger(__name__)


def _cosine_similarity_tfidf(
    text_a: str, text_b: str
) -> float:
    """
    Compute TF-IDF cosine similarity between two texts.

    Uses scikit-learn's TfidfVectorizer for lightweight
    vectorization without external embedding models.
    """
    if not text_a or not text_b:
        return 0.0

    try:
        from sklearn.feature_extraction.text import (
            TfidfVectorizer,
        )
        from sklearn.metrics.pairwise import (
            cosine_similarity,
        )

        vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
        )
        tfidf = vectorizer.fit_transform(
            [text_a, text_b]
        )
        score = cosine_similarity(
            tfidf[0:1], tfidf[1:2]
        )[0][0]
        return round(float(score), 4)

    except Exception:
        logger.exception(
            "TF-IDF similarity computation failed"
        )
        return 0.0


def _normalize_value(val) -> str:
    """Normalize a field value for comparison."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("value", ""))
    return str(val).strip()


class DocumentComparisonService:
    """Compare two documents across multiple dimensions."""

    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.ext_repo = ExtractionResultRepository(db)
        self.val_repo = ValidationResultRepository(db)
        self.content_repo = DocumentContentRepository(db)

    def compare(
        self,
        doc_id_a: str,
        doc_id_b: str,
    ) -> ComparisonResponse:
        """
        Compare two documents and return a structured diff.

        Args:
            doc_id_a: First document ID.
            doc_id_b: Second document ID.

        Returns:
            ComparisonResponse with diffs and scores.
        """

        # Fetch documents
        doc_a = self.doc_repo.get_by_id(doc_id_a)
        doc_b = self.doc_repo.get_by_id(doc_id_b)

        if not doc_a or not doc_b:
            raise ValueError(
                "One or both documents not found"
            )

        # Document types
        type_a = doc_a.document_type
        type_b = doc_b.document_type
        type_match = (
            type_a == type_b
            and type_a is not None
        )

        # Extraction results
        ext_a = self.ext_repo.get_by_document_id(
            doc_id_a
        )
        ext_b = self.ext_repo.get_by_document_id(
            doc_id_b
        )

        fields_a = (
            ext_a.extracted_fields or {}
        ) if ext_a else {}
        fields_b = (
            ext_b.extracted_fields or {}
        ) if ext_b else {}

        # Field-by-field diff
        all_field_names = sorted(
            set(fields_a.keys()) | set(fields_b.keys())
        )

        field_diffs = []
        for name in all_field_names:
            raw_a = fields_a.get(name)
            raw_b = fields_b.get(name)

            val_a = _normalize_value(raw_a)
            val_b = _normalize_value(raw_b)

            match = (
                val_a.lower() == val_b.lower()
                if val_a and val_b
                else val_a == val_b
            )

            notes = None
            if not match:
                if not val_a:
                    notes = "Missing in Document A"
                elif not val_b:
                    notes = "Missing in Document B"
                else:
                    notes = "Values differ"

            field_diffs.append(
                FieldDiff(
                    field_name=name,
                    value_a=val_a if val_a else None,
                    value_b=val_b if val_b else None,
                    match=match,
                    notes=notes,
                )
            )

        # Textual similarity
        content_a = (
            self.content_repo.get_by_document_id(
                doc_id_a
            )
        )
        content_b = (
            self.content_repo.get_by_document_id(
                doc_id_b
            )
        )

        text_a = (
            content_a.cleaned_text or ""
        ) if content_a else ""
        text_b = (
            content_b.cleaned_text or ""
        ) if content_b else ""

        similarity = _cosine_similarity_tfidf(
            text_a, text_b
        )

        # Validation status
        val_a_rec = (
            self.val_repo.get_by_document_id(
                doc_id_a
            )
        )
        val_b_rec = (
            self.val_repo.get_by_document_id(
                doc_id_b
            )
        )

        val_status_a = (
            val_a_rec.status
            if val_a_rec else "N/A"
        )
        val_status_b = (
            val_b_rec.status
            if val_b_rec else "N/A"
        )

        # Summary
        matching_fields = sum(
            1 for d in field_diffs if d.match
        )
        total_fields = len(field_diffs)
        summary = (
            f"Compared {total_fields} fields: "
            f"{matching_fields} match, "
            f"{total_fields - matching_fields} differ. "
            f"Text similarity: {similarity:.1%}. "
            f"Types: {'Match' if type_match else 'Different'}."
        )

        return ComparisonResponse(
            doc_id_a=doc_id_a,
            doc_id_b=doc_id_b,
            filename_a=doc_a.filename,
            filename_b=doc_b.filename,
            type_a=type_a,
            type_b=type_b,
            type_match=type_match,
            similarity_score=similarity,
            field_diffs=field_diffs,
            validation_a=val_status_a,
            validation_b=val_status_b,
            summary=summary,
        )
