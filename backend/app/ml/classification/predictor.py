"""
Document classification predictor.

Loads a trained TF-IDF + LogisticRegression model
from disk and predicts document types with confidence.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib

from app.ml.classification.preprocessing import (
    preprocess_for_classification,
)


logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of a document classification prediction."""

    document_type: str
    confidence: float


class DocumentClassifier:
    """
    Loads a trained classification model and
    predicts document types from text.

    Usage:
        classifier = DocumentClassifier()
        classifier.load("ml/artifacts/classification")
        result = classifier.predict("Invoice text...")
    """

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        fallback_class: str = "unclassified"
    ):

        self.confidence_threshold = (
            confidence_threshold
        )

        self.fallback_class = fallback_class

        self.vectorizer = None
        self.classifier = None
        self.is_loaded = False

    def load(
        self,
        model_dir: str
    ) -> bool:
        """
        Load vectorizer and classifier from disk.

        Args:
            model_dir: Path to the model artifacts
                       directory.

        Returns:
            True if model loaded successfully,
            False otherwise.
        """

        model_path = Path(model_dir)

        vectorizer_path = (
            model_path / "vectorizer.joblib"
        )

        classifier_path = (
            model_path / "classifier.joblib"
        )

        if not vectorizer_path.exists():

            logger.warning(
                "Vectorizer not found: %s",
                vectorizer_path
            )

            return False

        if not classifier_path.exists():

            logger.warning(
                "Classifier not found: %s",
                classifier_path
            )

            return False

        try:

            self.vectorizer = joblib.load(
                vectorizer_path
            )

            self.classifier = joblib.load(
                classifier_path
            )

            self.is_loaded = True

            logger.info(
                "Classification model loaded "
                "from %s",
                model_dir
            )

            return True

        except Exception:

            logger.exception(
                "Failed to load classification "
                "model from %s",
                model_dir
            )

            self.is_loaded = False

            return False

    def predict(
        self,
        text: str
    ) -> ClassificationResult:
        """
        Predict the document type from text.

        If no model is loaded, returns the
        fallback class with confidence 0.0.

        Args:
            text: Document text (raw or cleaned).

        Returns:
            ClassificationResult with document_type
            and confidence.
        """

        if not self.is_loaded:

            logger.warning(
                "No classification model loaded. "
                "Returning fallback class."
            )

            return ClassificationResult(
                document_type=self.fallback_class,
                confidence=0.0
            )

        preprocessed = (
            preprocess_for_classification(text)
        )

        if not preprocessed:

            return ClassificationResult(
                document_type=self.fallback_class,
                confidence=0.0
            )

        features = self.vectorizer.transform(
            [preprocessed]
        )

        probabilities = (
            self.classifier.predict_proba(
                features
            )[0]
        )

        max_index = probabilities.argmax()

        confidence = float(
            probabilities[max_index]
        )

        predicted_class = (
            self.classifier.classes_[max_index]
        )

        if confidence < self.confidence_threshold:

            return ClassificationResult(
                document_type=self.fallback_class,
                confidence=round(confidence, 4)
            )

        return ClassificationResult(
            document_type=predicted_class,
            confidence=round(confidence, 4)
        )
