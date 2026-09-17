"""
Validation engine base classes.

Defines the abstract ValidationRule interface,
ValidationResult data structure, and the
ValidationEngine that orchestrates rules.

All validation is deterministic — no ML or LLM
is used for arithmetic or business rule checks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ValidationStatus(str, Enum):
    """Overall validation status."""

    VALID = "VALID"
    INVALID = "INVALID"
    SKIPPED = "SKIPPED"


class RuleStatus(str, Enum):
    """Individual rule outcome."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class RuleResult:
    """Result of a single validation rule.

    Attributes:
        rule_code: Unique rule identifier
            (e.g. "TOTAL_MISMATCH").
        status: PASS, FAIL, WARN, or SKIP.
        message: Human-readable explanation.
        expected_value: What the rule expected.
        actual_value: What was found.
    """

    rule_code: str
    status: RuleStatus
    message: str = ""
    expected_value: Any = None
    actual_value: Any = None

    def to_dict(self) -> dict:
        return {
            "rule_code": self.rule_code,
            "status": self.status.value,
            "message": self.message,
            "expected_value": (
                str(self.expected_value)
                if self.expected_value is not None
                else None
            ),
            "actual_value": (
                str(self.actual_value)
                if self.actual_value is not None
                else None
            ),
        }


@dataclass
class ValidationResult:
    """Complete validation result for a document.

    Attributes:
        document_id: The document ID.
        document_type: Classified document type.
        status: Overall VALID / INVALID / SKIPPED.
        results: Individual rule results.
        validated_at: Timestamp.
    """

    document_id: str = ""
    document_type: str = ""
    status: ValidationStatus = (
        ValidationStatus.VALID
    )
    results: list[RuleResult] = field(
        default_factory=list
    )
    validated_at: datetime = field(
        default_factory=datetime.utcnow
    )

    @property
    def errors(self) -> list[RuleResult]:
        """All failed rules."""
        return [
            r
            for r in self.results
            if r.status == RuleStatus.FAIL
        ]

    @property
    def warnings(self) -> list[RuleResult]:
        """All warning rules."""
        return [
            r
            for r in self.results
            if r.status == RuleStatus.WARN
        ]

    @property
    def is_valid(self) -> bool:
        return self.status == ValidationStatus.VALID

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "status": self.status.value,
            "results": [
                r.to_dict() for r in self.results
            ],
            "validated_at": (
                self.validated_at.isoformat()
            ),
        }


class ValidationRule(ABC):
    """Abstract base class for validation rules.

    Each rule checks a specific business condition
    against extracted fields.
    """

    @property
    @abstractmethod
    def rule_code(self) -> str:
        """Unique identifier for this rule."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable rule description."""
        ...

    @abstractmethod
    def validate(
        self,
        extracted_fields: dict,
    ) -> RuleResult:
        """Run this rule against extracted fields.

        Args:
            extracted_fields: Dict mapping field
                names to their extracted values.
                Values are the raw field dicts from
                ExtractionResult (with "value",
                "confidence", "source" keys).

        Returns:
            RuleResult with the outcome.
        """
        ...


class ValidationEngine:
    """Orchestrates validation rules.

    Runs all registered rules against extracted
    fields and produces a ValidationResult.
    """

    def __init__(
        self,
        rules: list[ValidationRule] | None = None,
    ):

        self.rules: list[ValidationRule] = (
            rules or []
        )

    def add_rule(
        self, rule: ValidationRule
    ) -> None:
        """Register a validation rule."""
        self.rules.append(rule)

    def validate(
        self,
        document_id: str,
        document_type: str,
        extracted_fields: dict,
    ) -> ValidationResult:
        """Run all rules and produce a result.

        Args:
            document_id: The document ID.
            document_type: Classified document type.
            extracted_fields: Extraction output.

        Returns:
            ValidationResult with all rule outcomes.
        """

        if not self.rules:

            return ValidationResult(
                document_id=document_id,
                document_type=document_type,
                status=ValidationStatus.SKIPPED,
            )

        results: list[RuleResult] = []

        for rule in self.rules:

            try:
                result = rule.validate(
                    extracted_fields
                )
                results.append(result)

            except Exception as e:

                results.append(
                    RuleResult(
                        rule_code=rule.rule_code,
                        status=RuleStatus.SKIP,
                        message=(
                            f"Rule error: {e}"
                        ),
                    )
                )

        # Determine overall status
        has_failures = any(
            r.status == RuleStatus.FAIL
            for r in results
        )

        status = (
            ValidationStatus.INVALID
            if has_failures
            else ValidationStatus.VALID
        )

        return ValidationResult(
            document_id=document_id,
            document_type=document_type,
            status=status,
            results=results,
        )
