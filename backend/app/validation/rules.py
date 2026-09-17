"""
Invoice validation rules.

Deterministic business rules for validating
extracted invoice fields. No ML or LLM — only
arithmetic, date logic, and field presence checks.

All monetary comparisons use Decimal to avoid
floating-point errors.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any

from app.validation.base import (
    ValidationRule,
    RuleResult,
    RuleStatus,
)


# ------------------------------------------------
# Helpers
# ------------------------------------------------

def _get_field_value(
    fields: dict,
    field_name: str,
) -> Any:
    """Extract value from field dict.

    Fields are stored as:
        {"value": ..., "confidence": ..., ...}
    """

    field_data = fields.get(field_name)

    if field_data is None:
        return None

    if isinstance(field_data, dict):
        return field_data.get("value")

    return field_data


def _to_decimal(
    value: Any,
) -> Decimal | None:
    """Safely convert a value to Decimal.

    Returns None if conversion fails.
    """

    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


# ------------------------------------------------
# Rule: Required fields
# ------------------------------------------------

class RequiredFieldRule(ValidationRule):
    """Validates that required fields are present
    and non-empty.

    Configurable with a list of required field
    names.
    """

    def __init__(
        self,
        required_fields: list[str] | None = None,
    ):

        self._required = required_fields or [
            "invoice_number",
            "invoice_date",
            "total",
        ]

    @property
    def rule_code(self) -> str:
        return "REQUIRED_FIELDS"

    @property
    def description(self) -> str:
        return (
            "All required fields must be present "
            "and non-empty."
        )

    def validate(
        self,
        extracted_fields: dict,
    ) -> RuleResult:

        missing: list[str] = []

        for name in self._required:

            value = _get_field_value(
                extracted_fields, name
            )

            if value is None or str(value).strip() == "":
                missing.append(name)

        if missing:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.FAIL,
                message=(
                    "Missing required fields: "
                    + ", ".join(missing)
                ),
                expected_value=", ".join(
                    self._required
                ),
                actual_value=(
                    "missing: "
                    + ", ".join(missing)
                ),
            )

        return RuleResult(
            rule_code=self.rule_code,
            status=RuleStatus.PASS,
            message="All required fields present.",
        )


# ------------------------------------------------
# Rule: Subtotal + Tax = Total
# ------------------------------------------------

class SubtotalTaxTotalRule(ValidationRule):
    """Validates: subtotal + tax ≈ total.

    Uses Decimal arithmetic with configurable
    tolerance (default: ₹0.01).
    """

    def __init__(
        self,
        tolerance: Decimal | None = None,
    ):

        self.tolerance = (
            tolerance
            if tolerance is not None
            else Decimal("0.01")
        )

    @property
    def rule_code(self) -> str:
        return "TOTAL_MISMATCH"

    @property
    def description(self) -> str:
        return (
            "Subtotal plus tax/GST must equal "
            "total."
        )

    def validate(
        self,
        extracted_fields: dict,
    ) -> RuleResult:

        subtotal = _to_decimal(
            _get_field_value(
                extracted_fields, "subtotal"
            )
        )

        total = _to_decimal(
            _get_field_value(
                extracted_fields, "total"
            )
        )

        # Get tax (try both "tax" and "gst")
        tax = _to_decimal(
            _get_field_value(
                extracted_fields, "tax"
            )
        )

        gst = _to_decimal(
            _get_field_value(
                extracted_fields, "gst"
            )
        )

        # Use whichever tax value is available
        tax_value = tax or gst or Decimal("0")

        # Skip if we don't have both subtotal
        # and total
        if subtotal is None or total is None:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.SKIP,
                message=(
                    "Cannot verify total: "
                    "subtotal or total missing."
                ),
            )

        expected_total = subtotal + tax_value
        difference = abs(expected_total - total)

        if difference <= self.tolerance:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.PASS,
                message=(
                    "Total matches: "
                    f"{subtotal} + {tax_value} "
                    f"= {expected_total}"
                ),
                expected_value=str(expected_total),
                actual_value=str(total),
            )

        return RuleResult(
            rule_code=self.rule_code,
            status=RuleStatus.FAIL,
            message=(
                "Subtotal plus tax does not "
                f"equal total. Expected "
                f"{expected_total}, got {total} "
                f"(difference: {difference})"
            ),
            expected_value=str(expected_total),
            actual_value=str(total),
        )


# ------------------------------------------------
# Rule: Date consistency
# ------------------------------------------------

class DateConsistencyRule(ValidationRule):
    """Validates date logic:
    - Invoice date must not be in the far future
    - Due date must be on or after invoice date
    """

    @property
    def rule_code(self) -> str:
        return "DATE_INCONSISTENCY"

    @property
    def description(self) -> str:
        return (
            "Dates must be logically consistent."
        )

    def validate(
        self,
        extracted_fields: dict,
    ) -> RuleResult:

        invoice_date_str = _get_field_value(
            extracted_fields, "invoice_date"
        )

        due_date_str = _get_field_value(
            extracted_fields, "due_date"
        )

        if not invoice_date_str and not due_date_str:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.SKIP,
                message="No dates to validate.",
            )

        invoice_date = self._parse_date(
            invoice_date_str
        )

        due_date = self._parse_date(
            due_date_str
        )

        # Check invoice date not in far future
        if invoice_date:

            days_ahead = (
                invoice_date - datetime.utcnow()
            ).days

            if days_ahead > 365:

                return RuleResult(
                    rule_code=self.rule_code,
                    status=RuleStatus.FAIL,
                    message=(
                        "Invoice date is more "
                        "than 1 year in the "
                        "future."
                    ),
                    expected_value="within 1 year",
                    actual_value=str(
                        invoice_date_str
                    ),
                )

        # Check due date >= invoice date
        if invoice_date and due_date:

            if due_date < invoice_date:

                return RuleResult(
                    rule_code=self.rule_code,
                    status=RuleStatus.FAIL,
                    message=(
                        "Due date is before "
                        "invoice date."
                    ),
                    expected_value=(
                        f">= {invoice_date_str}"
                    ),
                    actual_value=str(
                        due_date_str
                    ),
                )

        return RuleResult(
            rule_code=self.rule_code,
            status=RuleStatus.PASS,
            message="Dates are consistent.",
        )

    def _parse_date(
        self, value: Any
    ) -> datetime | None:
        """Parse ISO date string."""

        if not value:
            return None

        try:
            return datetime.strptime(
                str(value), "%Y-%m-%d"
            )
        except ValueError:
            return None


# ------------------------------------------------
# Rule: Numeric validity
# ------------------------------------------------

class NumericValidityRule(ValidationRule):
    """Validates that amount fields contain
    valid numeric values (not NaN, not malformed).
    """

    def __init__(
        self,
        amount_fields: list[str] | None = None,
    ):

        self._fields = amount_fields or [
            "subtotal",
            "tax",
            "gst",
            "total",
        ]

    @property
    def rule_code(self) -> str:
        return "INVALID_NUMERIC"

    @property
    def description(self) -> str:
        return (
            "Amount fields must contain valid "
            "numeric values."
        )

    def validate(
        self,
        extracted_fields: dict,
    ) -> RuleResult:

        invalid_fields: list[str] = []

        for name in self._fields:

            value = _get_field_value(
                extracted_fields, name
            )

            if value is None:
                continue

            decimal_val = _to_decimal(value)

            if decimal_val is None:
                invalid_fields.append(
                    f"{name}={value}"
                )

        if invalid_fields:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.FAIL,
                message=(
                    "Invalid numeric values: "
                    + ", ".join(invalid_fields)
                ),
                expected_value="valid numbers",
                actual_value=", ".join(
                    invalid_fields
                ),
            )

        return RuleResult(
            rule_code=self.rule_code,
            status=RuleStatus.PASS,
            message=(
                "All numeric fields are valid."
            ),
        )


# ------------------------------------------------
# Rule: Negative / invalid amounts
# ------------------------------------------------

class NegativeAmountRule(ValidationRule):
    """Detects negative or zero amounts in fields
    where they are not expected.
    """

    def __init__(
        self,
        amount_fields: list[str] | None = None,
    ):

        self._fields = amount_fields or [
            "subtotal",
            "total",
        ]

    @property
    def rule_code(self) -> str:
        return "NEGATIVE_AMOUNT"

    @property
    def description(self) -> str:
        return (
            "Invoice amounts must be positive."
        )

    def validate(
        self,
        extracted_fields: dict,
    ) -> RuleResult:

        negative_fields: list[str] = []

        for name in self._fields:

            value = _get_field_value(
                extracted_fields, name
            )

            if value is None:
                continue

            decimal_val = _to_decimal(value)

            if decimal_val is not None:

                if decimal_val < Decimal("0"):
                    negative_fields.append(
                        f"{name}={decimal_val}"
                    )

        if negative_fields:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.FAIL,
                message=(
                    "Negative amounts detected: "
                    + ", ".join(negative_fields)
                ),
                expected_value=">= 0",
                actual_value=", ".join(
                    negative_fields
                ),
            )

        return RuleResult(
            rule_code=self.rule_code,
            status=RuleStatus.PASS,
            message="All amounts are non-negative.",
        )


# ------------------------------------------------
# Rule: Duplicate invoice number
# ------------------------------------------------

class DuplicateInvoiceNumberRule(ValidationRule):
    """Checks for duplicate invoice numbers
    in the database.

    Requires a lookup function that checks whether
    an invoice number already exists.
    """

    def __init__(
        self,
        lookup_fn=None,
    ):
        """
        Args:
            lookup_fn: Callable that takes
                (invoice_number, document_id) and
                returns True if a duplicate exists.
                If None, the rule is skipped.
        """

        self._lookup_fn = lookup_fn

    @property
    def rule_code(self) -> str:
        return "DUPLICATE_INVOICE_NUMBER"

    @property
    def description(self) -> str:
        return (
            "Invoice number must be unique."
        )

    def validate(
        self,
        extracted_fields: dict,
    ) -> RuleResult:

        if self._lookup_fn is None:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.SKIP,
                message=(
                    "Duplicate check not "
                    "available (no lookup "
                    "function)."
                ),
            )

        invoice_number = _get_field_value(
            extracted_fields, "invoice_number"
        )

        if not invoice_number:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.SKIP,
                message=(
                    "No invoice number to check."
                ),
            )

        document_id = _get_field_value(
            extracted_fields, "_document_id"
        )

        is_duplicate = self._lookup_fn(
            invoice_number, document_id
        )

        if is_duplicate:

            return RuleResult(
                rule_code=self.rule_code,
                status=RuleStatus.WARN,
                message=(
                    f"Duplicate invoice number: "
                    f"{invoice_number}"
                ),
                expected_value="unique",
                actual_value=str(invoice_number),
            )

        return RuleResult(
            rule_code=self.rule_code,
            status=RuleStatus.PASS,
            message="Invoice number is unique.",
        )


# ------------------------------------------------
# Factory: create default invoice rules
# ------------------------------------------------

def create_invoice_validation_rules(
    tolerance: Decimal | None = None,
    lookup_fn=None,
) -> list[ValidationRule]:
    """Create the standard set of invoice
    validation rules.

    Args:
        tolerance: Monetary tolerance for total
            matching (default: ₹0.01).
        lookup_fn: Optional duplicate check
            callable.

    Returns:
        List of configured ValidationRule instances.
    """

    return [
        RequiredFieldRule(),
        SubtotalTaxTotalRule(tolerance=tolerance),
        DateConsistencyRule(),
        NumericValidityRule(),
        NegativeAmountRule(),
        DuplicateInvoiceNumberRule(
            lookup_fn=lookup_fn
        ),
    ]
