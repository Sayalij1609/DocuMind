"""
Anomaly detection Pydantic schemas.

Response models for anomaly evaluation, feature breakdown,
and model training.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FeatureVectorResponse(BaseModel):
    """Extracted numerical features for a document."""

    document_id: str
    values: dict[str, float]
    missing_flags: dict[str, bool]
    feature_names: list[str]

    model_config = ConfigDict(from_attributes=True)


class AnomalyCheckResponse(BaseModel):
    """Response model for document anomaly detection."""

    document_id: str
    is_anomaly: bool
    anomaly_score: float
    decision_function_score: float
    features: dict[str, float]
    model_version: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyTrainResponse(BaseModel):
    """Response model for Isolation Forest model training."""

    status: str
    samples_trained: Optional[int] = None
    samples_available: Optional[int] = None
    samples_required: Optional[int] = None
    contamination: Optional[float] = None
    message: Optional[str] = None
    model_path: Optional[str] = None
    feature_names: Optional[list[str]] = None

    model_config = ConfigDict(from_attributes=True)
