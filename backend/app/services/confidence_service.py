"""
Confidence Score Service.

Aggregates confidence metrics from classification, extraction,
and validation stages into a weighted overall score with letter grade.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.confidence import (
    ConfidenceBreakdown,
    ConfidenceResponse,
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

logger = logging.getLogger(__name__)

# Stage weights for overall score
WEIGHTS = {
    "classification": 0.30,
    "extraction": 0.40,
    "validation": 0.30,
}


def _letter_grade(score: float) -> str:
    """Convert 0–100 score to letter grade."""
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


class ConfidenceService:
    """Compute unified confidence scores for a document."""

    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.ext_repo = ExtractionResultRepository(db)
        self.val_repo = ValidationResultRepository(db)

    def compute(
        self,
        document_id: str,
    ) -> ConfidenceResponse:
        """
        Compute confidence breakdown for a document.

        Returns overall weighted score (0–100) and
        per-stage breakdowns with letter grade.
        """

        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            raise ValueError("Document not found")

        breakdown = []

        # ── Classification Confidence ──
        cls_score = 0.0
        cls_details = "No classification result"

        if doc.classification_confidence is not None:
            cls_score = min(
                doc.classification_confidence * 100, 100.0
            )
            cls_details = (
                f"Type: {doc.document_type or 'unknown'}, "
                f"Raw: {doc.classification_confidence:.4f}"
            )

        cls_breakdown = ConfidenceBreakdown(
            stage="Classification",
            score=round(cls_score, 1),
            weight=WEIGHTS["classification"],
            weighted_score=round(
                cls_score * WEIGHTS["classification"], 1
            ),
            details=cls_details,
        )
        breakdown.append(cls_breakdown)

        # ── Extraction Confidence ──
        ext_score = 0.0
        ext_details = "No extraction result"

        ext_rec = self.ext_repo.get_by_document_id(
            document_id
        )
        if ext_rec and ext_rec.extracted_fields:
            fields = ext_rec.extracted_fields
            field_count = len(fields)

            if field_count > 0:
                confidences = []
                for fd in fields.values():
                    if isinstance(fd, dict):
                        c = fd.get("confidence", 0.0)
                    else:
                        c = 0.0
                    confidences.append(c)

                avg_conf = (
                    sum(confidences) / len(confidences)
                )
                ext_score = min(avg_conf * 100, 100.0)
                ext_details = (
                    f"{field_count} fields extracted, "
                    f"avg confidence: {avg_conf:.4f}"
                )

        ext_breakdown = ConfidenceBreakdown(
            stage="Extraction",
            score=round(ext_score, 1),
            weight=WEIGHTS["extraction"],
            weighted_score=round(
                ext_score * WEIGHTS["extraction"], 1
            ),
            details=ext_details,
        )
        breakdown.append(ext_breakdown)

        # ── Validation Confidence ──
        val_score = 0.0
        val_details = "No validation result"

        val_rec = self.val_repo.get_by_document_id(
            document_id
        )
        if val_rec and val_rec.rule_results:
            rules = val_rec.rule_results
            total = len(rules)
            passed = sum(
                1 for r in rules
                if r.get("status") == "PASS"
            )
            if total > 0:
                val_score = (passed / total) * 100
                val_details = (
                    f"{passed}/{total} rules passed"
                )

        val_breakdown = ConfidenceBreakdown(
            stage="Validation",
            score=round(val_score, 1),
            weight=WEIGHTS["validation"],
            weighted_score=round(
                val_score * WEIGHTS["validation"], 1
            ),
            details=val_details,
        )
        breakdown.append(val_breakdown)

        # ── Overall Score ──
        overall = sum(b.weighted_score for b in breakdown)
        overall = round(min(overall, 100.0), 1)

        return ConfidenceResponse(
            document_id=document_id,
            overall_score=overall,
            grade=_letter_grade(overall),
            classification=cls_breakdown,
            extraction=ext_breakdown,
            validation=val_breakdown,
            breakdown=breakdown,
        )
