"""
Pydantic schemas for Confidence Scores.
"""

from typing import Optional
from pydantic import BaseModel


class ConfidenceBreakdown(BaseModel):
    stage: str
    score: float
    weight: float
    weighted_score: float
    details: Optional[str] = None


class ConfidenceResponse(BaseModel):
    document_id: str
    overall_score: float
    grade: str
    classification: Optional[ConfidenceBreakdown] = None
    extraction: Optional[ConfidenceBreakdown] = None
    validation: Optional[ConfidenceBreakdown] = None
    breakdown: list[ConfidenceBreakdown] = []
