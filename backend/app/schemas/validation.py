"""
Validation Pydantic schemas.

Response models for the validation API endpoint.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RuleResultResponse(BaseModel):
    """Single validation rule result."""

    rule_code: str
    status: str
    message: str = ""
    expected_value: str | None = None
    actual_value: str | None = None


class ValidationResultResponse(BaseModel):
    """Validation result for a document."""

    document_id: str
    document_type: str
    status: str
    results: list[RuleResultResponse] = []
    validated_at: datetime | None = None
    error_count: int = 0
    warning_count: int = 0
