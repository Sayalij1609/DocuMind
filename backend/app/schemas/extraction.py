"""
Extraction Pydantic schemas.

Response models for extraction and LayoutLMv3
API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FieldResultResponse(BaseModel):
    """Single extracted field result."""

    value: Any = None
    confidence: float = 0.0
    source: str = "none"
    bbox: list[float] | None = None


class ExtractionResultResponse(BaseModel):
    """Extraction result for a document."""

    document_type: str
    fields: dict[str, FieldResultResponse]
    extraction_method: str
    extraction_version: str
    extracted_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ------------------------------------------------
# LayoutLMv3 response schemas (Phase 6)
# ------------------------------------------------

class LayoutLMEntityResponse(BaseModel):
    """A single entity predicted by LayoutLMv3."""

    label: str
    text: str
    confidence: float = 0.0
    bbox: list[int] | None = None


class LayoutLMPageResponse(BaseModel):
    """LayoutLMv3 predictions for a single page."""

    page_number: int
    entities: list[LayoutLMEntityResponse] = []


class LayoutLMResultResponse(BaseModel):
    """LayoutLMv3 analysis result."""

    model_name: str
    is_finetuned: bool = False
    pages: list[LayoutLMPageResponse] = []


class LayoutLMAnalysisResponse(BaseModel):
    """Dedicated LayoutLMv3 analysis endpoint
    response."""

    document_id: str
    model_name: str
    is_finetuned: bool = False
    pages: list[LayoutLMPageResponse] = []
    status: str = "completed"
    message: str = ""


# ------------------------------------------------
# Combined analysis response
# ------------------------------------------------

class DocumentAnalysisResponse(BaseModel):
    """Combined analysis response.

    Includes document metadata, classification,
    extraction results, and LayoutLMv3 predictions.
    """

    # Document metadata
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: datetime

    # Classification
    document_type: str | None = None
    classification_confidence: float | None = None
    classified_at: datetime | None = None

    # Extraction (Phase 5 — regex)
    extraction: ExtractionResultResponse | None = (
        None
    )

    # LayoutLMv3 (Phase 6)
    layoutlm: LayoutLMResultResponse | None = None

    # Validation (Phase 7)
    validation_status: str | None = None
    validation_error_count: int | None = None

    # Duplicate detection (Phase 8)
    has_duplicates: bool | None = None
    duplicate_count: int | None = None

    # Anomaly detection (Phase 9)
    is_anomaly: bool | None = None
    anomaly_score: float | None = None

    model_config = ConfigDict(
        from_attributes=True
    )
