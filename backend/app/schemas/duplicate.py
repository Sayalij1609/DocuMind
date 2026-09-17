"""
Duplicate detection Pydantic schemas.

Response models for the duplicate detection API.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DuplicateMatchResponse(BaseModel):
    """A single duplicate match."""

    matched_document_id: str
    similarity_score: float
    duplicate_type: str


class DuplicateCheckResponse(BaseModel):
    """Duplicate check result for a document."""

    document_id: str
    has_duplicates: bool = False
    exact_count: int = 0
    near_count: int = 0
    candidates_checked: int = 0
    matches: list[DuplicateMatchResponse] = []
