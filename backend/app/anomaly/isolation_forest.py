"""
Isolation Forest Anomaly Detector.

Wraps scikit-learn's IsolationForest for document-level anomaly detection.

=============================================================================
MATHEMATICAL BACKGROUND & EXPLANATION
=============================================================================

1. ISOLATION FOREST PRINCIPLE:
   Unlike distance- or density-based anomaly detectors, Isolation Forest isolates
   anomalies directly by randomly selecting a feature and randomly selecting a
   split value between the feature's min and max.
   - Normal points are densely clustered: require many splits to isolate.
   - Outliers are sparse and distant: require few splits to isolate (short path length).

2. CONTAMINATION:
   The proportion of outliers expected in the dataset (e.g. 0.05 = 5%).
   Controls the threshold on the decision function. When contamination="auto",
   the threshold is determined according to the original paper's heuristic.

3. ANOMALY SCORE vs. DECISION FUNCTION:
   - decision_function(X): The average path length offset by the threshold.
     * Values > 0 indicate INLIERS (normal documents).
     * Values < 0 indicate OUTLIERS (unusual / anomalous documents).
   - score_samples(X): Negative anomaly score. Lower scores indicate more
     abnormal samples.
   - Normalized anomaly score: In this module, we standardize the score so that
     higher values indicate higher anomalousness.

4. PREDICTION:
   predict(X) returns:
     * +1 for inliers (normal)
     * -1 for outliers (anomalous)

5. PROBABILITY WARNING:
   Isolation Forest outputs are relative isolation depths, NOT calibrated
   probabilities. They must not be interpreted as the probability of fraud
   or error unless calibrated with a labeled validation set.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from app.anomaly.base import (
    AnomalyDetector,
    FeatureVector,
)
from app.anomaly.features import FEATURE_NAMES


logger = logging.getLogger(__name__)


class IsolationForestDetector(AnomalyDetector):
    """Isolation Forest implementation for document anomaly detection.

    Attributes:
        contamination: Expected proportion of outliers (default: 0.05).
        n_estimators: Number of isolation trees (default: 100).
        random_state: Seed for reproducibility.
        feature_names: Expected list of feature names.
        min_samples: Minimum number of samples required to fit.
    """

    def __init__(
        self,
        contamination: float = 0.05,
        n_estimators: int = 100,
        random_state: int = 42,
        feature_names: list[str] | None = None,
        min_samples: int = 10,
        model_version: str = "isolation_forest_v1",
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_names = feature_names or list(FEATURE_NAMES)
        self.min_samples = min_samples
        self.model_version = model_version

        self._model: Optional[IsolationForest] = None
        self._is_fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        """Check if model has been trained and is ready for inference."""
        return self._is_fitted and self._model is not None

    def fit(
        self,
        feature_vectors: list[FeatureVector],
    ) -> "IsolationForestDetector":
        """Fit Isolation Forest on a collection of feature vectors.

        Args:
            feature_vectors: List of FeatureVector instances.

        Raises:
            ValueError: If number of vectors is below min_samples.
        """
        if len(feature_vectors) < self.min_samples:
            raise ValueError(
                f"Insufficient training data: received {len(feature_vectors)} "
                f"samples, but minimum required is {self.min_samples}."
            )

        X = np.array([fv.to_array() for fv in feature_vectors], dtype=np.float64)

        # Replace any NaN or Inf with 0.0 for safety
        X = np.nan_to_num(X, nan=0.0, posinf=1e9, neginf=-1e9)

        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        )
        model.fit(X)

        self._model = model
        self._is_fitted = True

        logger.info(
            "IsolationForest fitted on %d samples with contamination=%.3f",
            len(feature_vectors),
            self.contamination,
        )
        return self

    def predict(
        self,
        feature_vector: FeatureVector,
    ) -> tuple[bool, float, float]:
        """Predict whether a document is anomalous.

        Args:
            feature_vector: Document feature vector.

        Returns:
            Tuple of (is_anomaly, anomaly_score, decision_function_score).
            - is_anomaly: bool, True if flagged as unusual outlier.
            - anomaly_score: float, standardized score where higher indicates
              more anomalous.
            - decision_function_score: raw float, < 0 indicates anomaly.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted:
            raise RuntimeError(
                "IsolationForest model is not fitted. Fit or load a model first."
            )

        x = np.array([feature_vector.to_array()], dtype=np.float64)
        x = np.nan_to_num(x, nan=0.0, posinf=1e9, neginf=-1e9)

        # decision_function: positive = inlier, negative = outlier
        decision_score = float(self._model.decision_function(x)[0])

        # raw prediction: +1 for inlier, -1 for outlier
        pred = int(self._model.predict(x)[0])
        is_anomaly = pred == -1

        # score_samples returns opposite of anomaly score (higher = normal)
        # We invert it: higher = more anomalous
        raw_score = float(self._model.score_samples(x)[0])
        # raw_score is typically between -1.0 and 0.0. Anomaly score: -decision_score
        anomaly_score = -decision_score

        return is_anomaly, anomaly_score, decision_score

    def save(self, model_path: str) -> None:
        """Persist model and metadata to disk using joblib.

        Args:
            model_path: Target file path (.joblib).
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted IsolationForest model.")

        os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)

        payload = {
            "model": self._model,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "random_state": self.random_state,
            "feature_names": self.feature_names,
            "model_version": self.model_version,
            "min_samples": self.min_samples,
        }
        joblib.dump(payload, model_path)
        logger.info("Saved IsolationForest model to %s", model_path)

    def load(self, model_path: str) -> "IsolationForestDetector":
        """Load persisted model and metadata from disk.

        Args:
            model_path: Path to saved .joblib file.

        Returns:
            Self loaded with model weights.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Anomaly detection model file not found at: {model_path}"
            )

        payload = joblib.load(model_path)
        self._model = payload["model"]
        self.contamination = payload.get("contamination", self.contamination)
        self.n_estimators = payload.get("n_estimators", self.n_estimators)
        self.random_state = payload.get("random_state", self.random_state)
        self.feature_names = payload.get("feature_names", self.feature_names)
        self.model_version = payload.get("model_version", self.model_version)
        self.min_samples = payload.get("min_samples", self.min_samples)
        self._is_fitted = True

        logger.info("Loaded IsolationForest model from %s", model_path)
        return self

    @classmethod
    def create_synthetic_baseline(
        cls,
        n_samples: int = 50,
        contamination: float = 0.05,
        random_state: int = 42,
    ) -> "IsolationForestDetector":
        """Create and fit an IsolationForest on realistic synthetic baseline data.

        Useful for cold-start bootstrapping when an installation does not yet
        have sufficient historical documents to train a model.

        Synthetic distribution simulates typical business invoices:
        - invoice_amount: log-normal around $100–$10,000
        - tax_percentage: 5%–20% (e.g. GST/VAT)
        - document_length: 500–5,000 chars
        - word_count: 80–800 words
        - page_count: 1–3 pages
        - missing_field_count: 0–1
        - duplicate_similarity: 0.0–0.2
        - vendor_frequency: 1–10
        - validation_error_count: 0
        - item_count: 0
        """
        rng = np.random.RandomState(random_state)
        vectors: list[FeatureVector] = []

        for i in range(n_samples):
            # 95% standard invoices, 5% mild variance
            amount = float(np.exp(rng.normal(loc=7.5, scale=1.0)))  # ~$500 - $10,000
            tax_rate = float(rng.choice([5.0, 10.0, 12.0, 18.0, 20.0]))
            doc_len = float(rng.normal(loc=1500, scale=300))
            words = float(doc_len / 7.0)
            pages = float(rng.choice([1.0, 1.0, 1.0, 2.0, 3.0]))
            missing = float(rng.choice([0.0, 0.0, 0.0, 1.0]))
            dup_sim = float(rng.uniform(0.0, 0.15))
            vendor_freq = float(rng.randint(1, 15))
            val_err = 0.0
            item_cnt = 0.0

            vals = {
                "invoice_amount": max(10.0, amount),
                "tax_percentage": max(0.0, tax_rate),
                "document_length": max(100.0, doc_len),
                "word_count": max(20.0, words),
                "page_count": max(1.0, pages),
                "missing_field_count": missing,
                "duplicate_similarity": dup_sim,
                "vendor_frequency": vendor_freq,
                "validation_error_count": val_err,
                "item_count": item_cnt,
            }
            vectors.append(
                FeatureVector(
                    document_id=f"synth-{i}",
                    values=vals,
                    feature_names=list(FEATURE_NAMES),
                )
            )

        detector = cls(
            contamination=contamination,
            random_state=random_state,
            min_samples=10,
        )
        detector.fit(vectors)
        return detector
