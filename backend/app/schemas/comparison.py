"""
Pydantic schemas for Document Comparison.
"""

from typing import Optional

from pydantic import BaseModel


class ComparisonRequest(BaseModel):
    doc_id_a: str
    doc_id_b: str


class FieldDiff(BaseModel):
    field_name: str
    value_a: Optional[str] = None
    value_b: Optional[str] = None
    match: bool = False
    notes: Optional[str] = None


class ComparisonResponse(BaseModel):
    doc_id_a: str
    doc_id_b: str
    filename_a: Optional[str] = None
    filename_b: Optional[str] = None
    type_a: Optional[str] = None
    type_b: Optional[str] = None
    type_match: bool = False
    similarity_score: float = 0.0
    field_diffs: list[FieldDiff] = []
    validation_a: Optional[str] = None
    validation_b: Optional[str] = None
    summary: Optional[str] = None
