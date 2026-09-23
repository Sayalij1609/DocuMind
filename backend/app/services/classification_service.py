"""
Classification service.

Orchestrates document classification by combining
the ML predictor, financial heuristic rules, and AI validation
with the document repository.
"""

import logging
from typing import Optional

from app.ml.classification.predictor import (
    ClassificationResult,
    DocumentClassifier,
)
from app.ml.classification.heuristics import (
    FinancialHeuristicClassifier,
)
from app.services.document_repository import (
    DocumentRepository,
)

logger = logging.getLogger(__name__)


class ClassificationService:
    """
    Multi-Tier Hybrid Classification Service.

    Tier 1: High-confidence ML predictor (TF-IDF + SGD/LogisticRegression)
    Tier 2: Comprehensive Financial Heuristic Pattern Matcher
    Tier 3: AI Semantic Reconciliation
    """

    def __init__(
        self,
        classifier: DocumentClassifier,
        repository: DocumentRepository,
        heuristic_classifier: Optional[FinancialHeuristicClassifier] = None,
    ):
        self.classifier = classifier
        self.repository = repository
        self.heuristic_classifier = heuristic_classifier or FinancialHeuristicClassifier()

    def classify_document(
        self,
        document_id: str,
        document_text: str
    ) -> ClassificationResult:
        """
        Classify a document using hybrid ML + Heuristic approach and store the result.

        Args:
            document_id: ID of the document.
            document_text: Combined cleaned text from all pages.

        Returns:
            ClassificationResult with document_type and confidence.
        """
        # 1. Run ML classifier
        ml_result = self.classifier.predict(document_text)

        # 2. Run Financial Heuristic rules
        heuristic_match = self.heuristic_classifier.classify(document_text)

        # 3. Hybrid arbitration logic
        final_type = ml_result.document_type
        final_confidence = ml_result.confidence

        # Case A: Heuristic identified a specialized category that ML doesn't support
        # (e.g. bank_statement, salary_slip, utility_bill, receipt, tax_document, insurance)
        if heuristic_match and heuristic_match.document_type not in ["invoice", "purchase_order"]:
            final_type = heuristic_match.document_type
            final_confidence = max(final_confidence, heuristic_match.confidence)
            logger.info(
                "Document %s: Heuristic override '%s' (confidence: %.4f, score: %.1f)",
                document_id,
                final_type,
                final_confidence,
                heuristic_match.score,
            )

        # Case B: ML model returned unclassified or other, but heuristics identified a category
        elif ml_result.document_type in ["unclassified", "other"] and heuristic_match:
            final_type = heuristic_match.document_type
            final_confidence = heuristic_match.confidence
            logger.info(
                "Document %s: Unclassified ML promoted to '%s' via heuristic (confidence: %.4f)",
                document_id,
                final_type,
                final_confidence,
            )

        # Case C: Both ML and heuristic agree on invoice or purchase_order
        elif heuristic_match and heuristic_match.document_type == ml_result.document_type:
            final_confidence = min(0.99, max(ml_result.confidence, heuristic_match.confidence) + 0.05)

        # Case D: ML is confident (>= 0.75) and heuristic is weak
        elif ml_result.confidence >= 0.75:
            final_type = ml_result.document_type
            final_confidence = ml_result.confidence

        # Case E: Heuristic has higher confidence than weak ML
        elif heuristic_match and heuristic_match.confidence > ml_result.confidence:
            final_type = heuristic_match.document_type
            final_confidence = heuristic_match.confidence

        result = ClassificationResult(
            document_type=final_type,
            confidence=round(final_confidence, 4),
        )

        logger.info(
            "Document %s final classification: '%s' (confidence: %.4f)",
            document_id,
            result.document_type,
            result.confidence,
        )

        self.repository.update_classification(
            document_id=document_id,
            document_type=result.document_type,
            confidence=result.confidence,
        )

        return result

    def update_from_ai(
        self,
        document_id: str,
        ai_detected_type: str,
        confidence: float = 0.92,
    ) -> None:
        """
        Reconcile classification with verified AI semantic output if current classification
        is unclassified or was an ambiguous guess.
        """
        if not ai_detected_type or ai_detected_type in ["unclassified", "unknown", "other"]:
            return

        doc = self.repository.get_by_id(document_id)
        if not doc:
            return

        current_type = doc.document_type or "unclassified"
        current_conf = doc.classification_confidence or 0.0

        # Only override if currently unclassified, or confidence was below 0.65
        if current_type in ["unclassified", "other"] or current_conf < 0.65:
            logger.info(
                "Document %s reclassified via AI: '%s' -> '%s' (confidence: %.4f)",
                document_id,
                current_type,
                ai_detected_type,
                confidence,
            )
            self.repository.update_classification(
                document_id=document_id,
                document_type=ai_detected_type,
                confidence=confidence,
            )
