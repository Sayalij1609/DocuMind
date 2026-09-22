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

    # AI Semantic Analysis (Phase 11)
    ai_analysis: dict | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


# ------------------------------------------------
# AI Analysis response schemas (Phase 11)
# ------------------------------------------------

class AIAnalysisResponse(BaseModel):
    """Full AI semantic analysis result."""

    executive_summary: str = ""
    document_type: str = "unknown"
    entities: dict = {}
    relationships: list[dict] = []
    line_items: list[dict] = []
    financial_validation: dict = {}
    risk_narrative: str = ""
    insights: list[str] = []
    validation_summary: str = ""
    duplicate_assessment: str = ""
    anomaly_assessment: str = ""
    analysis_method: str = "none"
    analyzed_at: str | None = None


class SourceCitation(BaseModel):
    """Structured attribution source for RAG."""

    document_id: str
    filename: str = "Document"
    page_number: int = 1
    chunk_id: str = ""
    chunk_type: str = "page_text"
    snippet: str = ""
    similarity_score: float = 0.0


class DocumentQARequest(BaseModel):
    """Request body for single-document Q&A."""

    question: str


class MultiDocumentQARequest(BaseModel):
    """Request body for multi-document / repository-wide Q&A."""

    question: str
    document_ids: list[str] | None = None


class DocumentQAResponse(BaseModel):
    """Response for document Q&A with structured sources and citations."""

    answer: str
    sources: list[SourceCitation] = []
    citations: list[str] = []
    method: str = "rag"


class AIConfigRequest(BaseModel):
    """Request to update AI config at runtime."""
    api_key: str


class AIStatusResponse(BaseModel):
    """AI configuration status."""

    configured: bool = False
    model: str = ""
    source: str = "none"

