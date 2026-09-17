"""
Anomaly detection base classes and interfaces.

Defines the core data structures and abstract base classes for
unsupervised document anomaly detection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class FeatureVector:
    """Structured feature vector representing a document.

    Attributes:
        document_id: Unique identifier for the document.
        values: Numerical feature values as a dict mapping name -> float.
        feature_names: Ordered list of feature names.
        missing_flags: Mapping of feature_name -> bool indicating whether
            the feature was imputed / missing in the source data.
        metadata: Supplementary contextual details.
    """

    document_id: str
    values: dict[str, float]
    feature_names: list[str] = field(default_factory=list)
    missing_flags: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_array(self) -> list[float]:
        """Convert features to ordered numerical array."""
        if not self.feature_names:
            self.feature_names = sorted(self.values.keys())
        return [float(self.values.get(name, 0.0)) for name in self.feature_names]

    def to_dict(self) -> dict[str, Any]:
        """Serialize feature vector to dict."""
        return {
            "document_id": self.document_id,
            "values": self.values,
            "feature_names": self.feature_names or sorted(self.values.keys()),
            "missing_flags": self.missing_flags,
            "metadata": self.metadata,
        }


@dataclass
class AnomalyResult:
    """Result of an anomaly detection evaluation.

    Terminology strictly uses outlier / unusual / anomalous,
    never fraud.

    Attributes:
        document_id: Unique identifier for the evaluated document.
        is_anomaly: True if the document is flagged as an unusual outlier.
        anomaly_score: Relative anomaly score. Higher values indicate
            greater isolation / abnormality.
        decision_function_score: Raw decision function output from model.
            Typically positive for inliers and negative for outliers.
        features: Snapshot of extracted features used for decision.
        model_version: Model identifier or version string.
        detected_at: Timestamp when anomaly check was performed.
    """

    document_id: str
    is_anomaly: bool
    anomaly_score: float
    decision_function_score: float
    features: dict[str, float]
    model_version: str = "isolation_forest_v1"
    detected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize anomaly result to dict."""
        return {
            "document_id": self.document_id,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": round(self.anomaly_score, 4),
            "decision_function_score": round(
                self.decision_function_score, 4
            ),
            "features": self.features,
            "model_version": self.model_version,
            "detected_at": (
                self.detected_at.isoformat()
                if isinstance(self.detected_at, datetime)
                else self.detected_at
            ),
        }


class AnomalyDetector(ABC):
    """Abstract interface for anomaly detection models."""

    @abstractmethod
    def fit(self, feature_vectors: list[FeatureVector]) -> "AnomalyDetector":
        """Train the anomaly detector on a collection of feature vectors."""
        ...

    @abstractmethod
    def predict(
        self, feature_vector: FeatureVector
    ) -> tuple[bool, float, float]:
        """Predict whether a feature vector is anomalous.

        Returns:
            Tuple of (is_anomaly, anomaly_score, decision_function_score).
        """
        ...

    @abstractmethod
    def save(self, model_path: str) -> None:
        """Persist model artifacts to disk."""
        ...

    @abstractmethod
    def load(self, model_path: str) -> "AnomalyDetector":
        """Load model artifacts from disk."""
        ...

    @property
    @abstractmethod
    def is_fitted(self) -> bool:
        """Check if model has been fitted."""
        ...
