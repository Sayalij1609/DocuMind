"""
Tests for Phase 4 — Document Classification.

Covers:
1. Text preprocessing
2. Empty text handling
3. Model prediction
4. Confidence threshold
5. Graceful fallback (no model)
6. Metrics computation
7. Classification service
8. API schema response
"""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from app.ml.classification.preprocessing import (
    preprocess_for_classification,
)

from app.ml.classification.predictor import (
    ClassificationResult,
    DocumentClassifier,
)

from app.ml.classification.metrics import (
    compute_metrics,
)

from app.services.classification_service import (
    ClassificationService,
)

from app.schemas.document import (
    DocumentResponse,
)


# =========================================================
# Preprocessing
# =========================================================

class TestPreprocessing:

    def test_lowercase(self):
        """Text should be lowercased."""

        result = preprocess_for_classification(
            "INVOICE NUMBER"
        )

        assert result == "invoice number"

    def test_whitespace_normalization(self):
        """
        Multiple spaces should be collapsed
        to a single space.
        """

        result = preprocess_for_classification(
            "invoice    number    123"
        )

        assert result == "invoice number 123"

    def test_newline_normalization(self):
        """
        Excessive newlines should be collapsed
        to double newline.
        """

        result = preprocess_for_classification(
            "line1\n\n\n\n\nline2"
        )

        assert result == "line1\n\nline2"

    def test_empty_text(self):
        """Empty text should return empty string."""

        assert preprocess_for_classification("") == ""
        assert preprocess_for_classification(None) == ""

    def test_preserves_numbers(self):
        """
        Numbers should be preserved —
        they help distinguish document types.
        """

        result = preprocess_for_classification(
            "Total: $1,234.56"
        )

        assert "1,234.56" in result

    def test_preserves_financial_tokens(self):
        """
        Financial tokens like GST, INV, PO
        should be preserved (lowercased).
        """

        result = preprocess_for_classification(
            "GST: 18% INV-2024-001 PO#456"
        )

        assert "gst" in result
        assert "inv-2024-001" in result
        assert "po#456" in result

    def test_preserves_dates(self):
        """
        Date patterns should be preserved.
        """

        result = preprocess_for_classification(
            "Date: 01/15/2024"
        )

        assert "01/15/2024" in result

    def test_repeated_punctuation_collapsed(self):
        """
        Excessive punctuation should be collapsed.
        """

        result = preprocess_for_classification(
            "total-----amount"
        )

        assert "-----" not in result
        assert "-" in result

    def test_carriage_return_normalized(self):
        """
        \\r\\n should be normalized to \\n.
        """

        result = preprocess_for_classification(
            "line1\r\nline2"
        )

        assert "\r" not in result
        assert "line1\nline2" == result


# =========================================================
# Predictor — no model loaded
# =========================================================

class TestPredictorNoModel:

    def test_fallback_when_no_model(self):
        """
        When no model is loaded, should return
        fallback class with 0.0 confidence.
        """

        classifier = DocumentClassifier(
            confidence_threshold=0.5,
            fallback_class="unclassified"
        )

        result = classifier.predict(
            "Some invoice text"
        )

        assert result.document_type == "unclassified"
        assert result.confidence == 0.0

    def test_is_loaded_false_by_default(self):
        """
        Classifier should not be loaded
        by default.
        """

        classifier = DocumentClassifier()

        assert classifier.is_loaded is False

    def test_load_nonexistent_dir(self):
        """
        Loading from a nonexistent directory
        should return False.
        """

        classifier = DocumentClassifier()

        loaded = classifier.load(
            "/nonexistent/path"
        )

        assert loaded is False
        assert classifier.is_loaded is False


# =========================================================
# Predictor — with mock model
# =========================================================

class TestPredictorWithModel:

    def _create_loaded_classifier(
        self,
        predicted_class="invoice",
        confidence=0.92,
        threshold=0.5
    ):
        """Helper to create a classifier with mocked internals."""

        import numpy as np

        classifier = DocumentClassifier(
            confidence_threshold=threshold,
            fallback_class="unclassified"
        )

        mock_vectorizer = MagicMock()
        mock_vectorizer.transform.return_value = (
            MagicMock()
        )

        mock_clf = MagicMock()
        mock_clf.classes_ = np.array([
            "invoice", "other", "purchase_order"
        ])

        probs = np.zeros(3)
        class_idx = list(
            mock_clf.classes_
        ).index(predicted_class)
        probs[class_idx] = confidence

        remaining = 1.0 - confidence
        for i in range(3):
            if i != class_idx:
                probs[i] = remaining / 2

        mock_clf.predict_proba.return_value = (
            np.array([probs])
        )

        classifier.vectorizer = mock_vectorizer
        classifier.classifier = mock_clf
        classifier.is_loaded = True

        return classifier

    def test_predict_returns_result(self):
        """
        Predict should return a
        ClassificationResult.
        """

        classifier = self._create_loaded_classifier(
            predicted_class="invoice",
            confidence=0.92
        )

        result = classifier.predict(
            "Invoice number 12345"
        )

        assert isinstance(
            result, ClassificationResult
        )

        assert result.document_type == "invoice"
        assert result.confidence == 0.92

    def test_confidence_threshold_applied(self):
        """
        When confidence is below threshold,
        should return fallback class.
        """

        classifier = self._create_loaded_classifier(
            predicted_class="invoice",
            confidence=0.4,
            threshold=0.5
        )

        result = classifier.predict(
            "Unclear document text"
        )

        assert result.document_type == "unclassified"
        assert result.confidence == 0.4

    def test_confidence_above_threshold(self):
        """
        When confidence is above threshold,
        should return predicted class.
        """

        classifier = self._create_loaded_classifier(
            predicted_class="purchase_order",
            confidence=0.88,
            threshold=0.5
        )

        result = classifier.predict(
            "Purchase order number PO-2024"
        )

        assert result.document_type == (
            "purchase_order"
        )

        assert result.confidence == 0.88

    def test_empty_text_returns_fallback(self):
        """
        Empty text should return fallback class.
        """

        classifier = self._create_loaded_classifier()

        result = classifier.predict("")

        assert result.document_type == "unclassified"
        assert result.confidence == 0.0


# =========================================================
# Metrics
# =========================================================

class TestMetrics:

    def test_perfect_predictions(self):
        """
        Perfect predictions should give 1.0
        for all metrics.
        """

        y_true = [
            "invoice", "invoice",
            "other", "other",
            "purchase_order", "purchase_order"
        ]

        y_pred = y_true.copy()

        metrics = compute_metrics(
            y_true, y_pred,
            labels=[
                "invoice", "other",
                "purchase_order"
            ]
        )

        assert metrics["accuracy"] == 1.0
        assert metrics["f1_macro"] == 1.0

    def test_metrics_structure(self):
        """
        Metrics dict should have all expected keys.
        """

        y_true = ["invoice", "other"]
        y_pred = ["invoice", "invoice"]

        metrics = compute_metrics(
            y_true, y_pred
        )

        assert "accuracy" in metrics
        assert "precision_macro" in metrics
        assert "recall_macro" in metrics
        assert "f1_macro" in metrics
        assert "confusion_matrix" in metrics
        assert "labels" in metrics
        assert "classification_report" in metrics

    def test_confusion_matrix_shape(self):
        """
        Confusion matrix should be square
        with size = number of classes.
        """

        y_true = [
            "invoice", "other",
            "purchase_order"
        ]

        y_pred = [
            "invoice", "other",
            "purchase_order"
        ]

        labels = [
            "invoice", "other",
            "purchase_order"
        ]

        metrics = compute_metrics(
            y_true, y_pred,
            labels=labels
        )

        matrix = metrics["confusion_matrix"]

        assert len(matrix) == 3
        assert len(matrix[0]) == 3


# =========================================================
# Classification Service
# =========================================================

class TestClassificationService:

    def test_classify_document(self):
        """
        Service should call predictor and
        update repository.
        """

        mock_classifier = MagicMock()
        mock_classifier.predict.return_value = (
            ClassificationResult(
                document_type="invoice",
                confidence=0.94
            )
        )

        mock_repository = MagicMock()

        service = ClassificationService(
            classifier=mock_classifier,
            repository=mock_repository
        )

        result = service.classify_document(
            document_id="doc-123",
            document_text="Invoice text"
        )

        assert result.document_type == "invoice"
        assert result.confidence == 0.94

        mock_classifier.predict.assert_called_once_with(
            "Invoice text"
        )

        mock_repository.update_classification.assert_called_once_with(
            document_id="doc-123",
            document_type="invoice",
            confidence=0.94
        )


# =========================================================
# Schema response
# =========================================================

class TestSchemaResponse:

    def test_classification_fields_in_response(self):
        """
        DocumentResponse should include
        classification fields.
        """

        response = DocumentResponse(
            document_id="doc-123",
            filename="invoice.pdf",
            file_type=".pdf",
            file_size=12345,
            file_path="/path/to/file",
            status="completed",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            document_type="invoice",
            classification_confidence=0.94,
            classified_at="2024-01-01T00:01:00"
        )

        assert response.document_type == "invoice"
        assert response.classification_confidence == 0.94
        assert response.classified_at is not None

    def test_classification_fields_nullable(self):
        """
        Classification fields should be
        optional (None by default).
        """

        response = DocumentResponse(
            document_id="doc-123",
            filename="invoice.pdf",
            file_type=".pdf",
            file_size=12345,
            file_path="/path/to/file",
            status="uploaded",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )

        assert response.document_type is None
        assert response.classification_confidence is None
        assert response.classified_at is None
