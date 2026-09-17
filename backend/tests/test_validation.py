"""
Unit tests for Phase 7 — Deterministic Validation Engine.

Tests:
- Individual validation rules
- Decimal precision for monetary amounts
- Valid invoices
- Invalid totals
- Missing fields
- Date consistency
- Malformed amounts
- Negative amounts
- Tolerance handling
- Engine orchestration
- BIO grouping of results
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.validation.base import (
    ValidationEngine,
    ValidationResult,
    ValidationStatus,
    ValidationRule,
    RuleResult,
    RuleStatus,
)

from app.validation.rules import (
    RequiredFieldRule,
    SubtotalTaxTotalRule,
    DateConsistencyRule,
    NumericValidityRule,
    NegativeAmountRule,
    DuplicateInvoiceNumberRule,
    create_invoice_validation_rules,
    _get_field_value,
    _to_decimal,
)


# ====================================================
# Helper: build field dict
# ====================================================

def _fields(**kwargs) -> dict:
    """Build an extracted_fields dict."""
    return {
        k: {"value": v, "confidence": 0.9, "source": "regex"}
        for k, v in kwargs.items()
    }


# ====================================================
# Helpers tests
# ====================================================

class TestHelpers:

    def test_get_field_value_from_dict(self):
        fields = {"total": {"value": "100", "confidence": 0.9}}
        assert _get_field_value(fields, "total") == "100"

    def test_get_field_value_missing(self):
        assert _get_field_value({}, "total") is None

    def test_get_field_value_raw(self):
        # Non-dict value (edge case)
        fields = {"total": "100"}
        assert _get_field_value(fields, "total") == "100"

    def test_to_decimal_valid(self):
        assert _to_decimal("85500") == Decimal("85500")
        assert _to_decimal("100.50") == Decimal("100.50")
        assert _to_decimal(100) == Decimal("100")

    def test_to_decimal_none(self):
        assert _to_decimal(None) is None

    def test_to_decimal_invalid(self):
        assert _to_decimal("not_a_number") is None
        assert _to_decimal("") is None


# ====================================================
# RequiredFieldRule tests
# ====================================================

class TestRequiredFieldRule:

    def test_all_present(self):
        fields = _fields(
            invoice_number="INV-001",
            invoice_date="2026-09-01",
            total="100890",
        )
        rule = RequiredFieldRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_missing_invoice_number(self):
        fields = _fields(
            invoice_date="2026-09-01",
            total="100890",
        )
        rule = RequiredFieldRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert "invoice_number" in result.message

    def test_missing_total(self):
        fields = _fields(
            invoice_number="INV-001",
            invoice_date="2026-09-01",
        )
        rule = RequiredFieldRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert "total" in result.message

    def test_all_missing(self):
        rule = RequiredFieldRule()
        result = rule.validate({})
        assert result.status == RuleStatus.FAIL

    def test_empty_value(self):
        fields = _fields(
            invoice_number="",
            invoice_date="2026-09-01",
            total="100",
        )
        rule = RequiredFieldRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert "invoice_number" in result.message

    def test_none_value(self):
        fields = {
            "invoice_number": {"value": None},
            "invoice_date": {"value": "2026-09-01"},
            "total": {"value": "100"},
        }
        rule = RequiredFieldRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL

    def test_custom_required_fields(self):
        rule = RequiredFieldRule(
            required_fields=["vendor", "total"]
        )
        fields = _fields(
            vendor="Acme",
            total="100",
        )
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS


# ====================================================
# SubtotalTaxTotalRule tests
# ====================================================

class TestSubtotalTaxTotalRule:

    def test_valid_total(self):
        """85500 + 15390 = 100890"""
        fields = _fields(
            subtotal="85500",
            tax="15390",
            total="100890",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_valid_with_decimals(self):
        """1000.50 + 180.09 = 1180.59"""
        fields = _fields(
            subtotal="1000.50",
            tax="180.09",
            total="1180.59",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_invalid_total(self):
        """85500 + 15000 != 100890"""
        fields = _fields(
            subtotal="85500",
            tax="15000",
            total="100890",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert result.rule_code == "TOTAL_MISMATCH"

    def test_uses_gst_when_no_tax(self):
        """85500 + 15390 (gst) = 100890"""
        fields = _fields(
            subtotal="85500",
            gst="15390",
            total="100890",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_missing_subtotal_skips(self):
        fields = _fields(
            tax="15390",
            total="100890",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.SKIP

    def test_missing_total_skips(self):
        fields = _fields(
            subtotal="85500",
            tax="15390",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.SKIP

    def test_no_tax_is_zero(self):
        """subtotal + 0 = total when no tax"""
        fields = _fields(
            subtotal="100",
            total="100",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_tolerance_within(self):
        """100.001 vs 100.00 within tolerance"""
        fields = _fields(
            subtotal="100",
            total="100.001",
        )
        rule = SubtotalTaxTotalRule(
            tolerance=Decimal("0.01")
        )
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_tolerance_exceeded(self):
        """100.5 vs 100.0 exceeds 0.01 tolerance"""
        fields = _fields(
            subtotal="100",
            total="100.5",
        )
        rule = SubtotalTaxTotalRule(
            tolerance=Decimal("0.01")
        )
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL

    def test_custom_tolerance(self):
        """Custom tolerance of 1.0"""
        fields = _fields(
            subtotal="100",
            total="100.5",
        )
        rule = SubtotalTaxTotalRule(
            tolerance=Decimal("1.0")
        )
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_decimal_precision(self):
        """Ensures no float equality issues.
        0.1 + 0.2 must equal 0.3 exactly."""
        fields = _fields(
            subtotal="0.1",
            tax="0.2",
            total="0.3",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_large_amounts(self):
        """10000000 + 1800000 = 11800000"""
        fields = _fields(
            subtotal="10000000",
            tax="1800000",
            total="11800000",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_expected_actual_in_result(self):
        fields = _fields(
            subtotal="100",
            tax="18",
            total="120",
        )
        rule = SubtotalTaxTotalRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert result.expected_value == "118"
        assert result.actual_value == "120"


# ====================================================
# DateConsistencyRule tests
# ====================================================

class TestDateConsistencyRule:

    def test_valid_dates(self):
        fields = _fields(
            invoice_date="2026-09-01",
            due_date="2026-09-30",
        )
        rule = DateConsistencyRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_same_day(self):
        fields = _fields(
            invoice_date="2026-09-01",
            due_date="2026-09-01",
        )
        rule = DateConsistencyRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_due_before_invoice(self):
        fields = _fields(
            invoice_date="2026-09-30",
            due_date="2026-09-01",
        )
        rule = DateConsistencyRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert "before" in result.message.lower()

    def test_no_dates_skips(self):
        rule = DateConsistencyRule()
        result = rule.validate({})
        assert result.status == RuleStatus.SKIP

    def test_only_invoice_date(self):
        fields = _fields(
            invoice_date="2026-09-01",
        )
        rule = DateConsistencyRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_malformed_date(self):
        fields = _fields(
            invoice_date="not-a-date",
            due_date="2026-09-30",
        )
        rule = DateConsistencyRule()
        result = rule.validate(fields)
        # Can't parse, so can't compare — passes
        assert result.status == RuleStatus.PASS


# ====================================================
# NumericValidityRule tests
# ====================================================

class TestNumericValidityRule:

    def test_all_valid(self):
        fields = _fields(
            subtotal="85500",
            tax="15390",
            total="100890",
        )
        rule = NumericValidityRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_malformed_amount(self):
        fields = _fields(
            subtotal="abc",
            total="100",
        )
        rule = NumericValidityRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert "subtotal" in result.message

    def test_missing_field_ok(self):
        """Missing fields don't trigger failure."""
        fields = _fields(total="100")
        rule = NumericValidityRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_empty_fields(self):
        rule = NumericValidityRule()
        result = rule.validate({})
        assert result.status == RuleStatus.PASS

    def test_decimal_values(self):
        fields = _fields(
            subtotal="1000.50",
            tax="180.09",
            total="1180.59",
        )
        rule = NumericValidityRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS


# ====================================================
# NegativeAmountRule tests
# ====================================================

class TestNegativeAmountRule:

    def test_positive_amounts(self):
        fields = _fields(
            subtotal="100",
            total="118",
        )
        rule = NegativeAmountRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_negative_total(self):
        fields = _fields(
            subtotal="100",
            total="-50",
        )
        rule = NegativeAmountRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL
        assert "total" in result.message.lower()

    def test_negative_subtotal(self):
        fields = _fields(
            subtotal="-100",
            total="0",
        )
        rule = NegativeAmountRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.FAIL

    def test_zero_is_ok(self):
        fields = _fields(
            subtotal="0",
            total="0",
        )
        rule = NegativeAmountRule()
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_missing_is_ok(self):
        rule = NegativeAmountRule()
        result = rule.validate({})
        assert result.status == RuleStatus.PASS


# ====================================================
# DuplicateInvoiceNumberRule tests
# ====================================================

class TestDuplicateInvoiceNumberRule:

    def test_no_lookup_fn_skips(self):
        rule = DuplicateInvoiceNumberRule()
        fields = _fields(invoice_number="INV-001")
        result = rule.validate(fields)
        assert result.status == RuleStatus.SKIP

    def test_unique_number(self):
        rule = DuplicateInvoiceNumberRule(
            lookup_fn=lambda num, doc_id: False
        )
        fields = _fields(invoice_number="INV-001")
        result = rule.validate(fields)
        assert result.status == RuleStatus.PASS

    def test_duplicate_found(self):
        rule = DuplicateInvoiceNumberRule(
            lookup_fn=lambda num, doc_id: True
        )
        fields = _fields(invoice_number="INV-001")
        result = rule.validate(fields)
        assert result.status == RuleStatus.WARN

    def test_no_invoice_number_skips(self):
        rule = DuplicateInvoiceNumberRule(
            lookup_fn=lambda num, doc_id: False
        )
        result = rule.validate({})
        assert result.status == RuleStatus.SKIP


# ====================================================
# ValidationEngine tests
# ====================================================

class TestValidationEngine:

    def test_valid_invoice(self):
        fields = _fields(
            invoice_number="INV-001",
            invoice_date="2026-09-01",
            due_date="2026-09-30",
            subtotal="85500",
            tax="15390",
            total="100890",
        )
        rules = create_invoice_validation_rules()
        engine = ValidationEngine(rules=rules)
        result = engine.validate(
            "doc-1", "invoice", fields
        )
        assert result.status == ValidationStatus.VALID
        assert len(result.errors) == 0

    def test_invalid_total(self):
        fields = _fields(
            invoice_number="INV-001",
            invoice_date="2026-09-01",
            subtotal="85500",
            tax="15000",
            total="100890",
        )
        rules = create_invoice_validation_rules()
        engine = ValidationEngine(rules=rules)
        result = engine.validate(
            "doc-1", "invoice", fields
        )
        assert result.status == ValidationStatus.INVALID
        assert any(
            r.rule_code == "TOTAL_MISMATCH"
            for r in result.errors
        )

    def test_missing_required_fields(self):
        fields = _fields(
            subtotal="100",
        )
        rules = create_invoice_validation_rules()
        engine = ValidationEngine(rules=rules)
        result = engine.validate(
            "doc-1", "invoice", fields
        )
        assert result.status == ValidationStatus.INVALID
        assert any(
            r.rule_code == "REQUIRED_FIELDS"
            for r in result.errors
        )

    def test_no_rules_skips(self):
        engine = ValidationEngine()
        result = engine.validate(
            "doc-1", "invoice", {}
        )
        assert result.status == ValidationStatus.SKIPPED

    def test_rule_exception_handled(self):
        """Rule that throws should not crash engine."""

        class BrokenRule(ValidationRule):
            @property
            def rule_code(self):
                return "BROKEN"

            @property
            def description(self):
                return "Always fails"

            def validate(self, fields):
                raise RuntimeError("boom")

        engine = ValidationEngine(
            rules=[BrokenRule()]
        )
        result = engine.validate(
            "doc-1", "invoice", {}
        )
        # Exception caught, rule SKIPped
        assert result.status == ValidationStatus.VALID
        assert result.results[0].status == RuleStatus.SKIP
        assert "boom" in result.results[0].message

    def test_multiple_errors(self):
        """Missing fields AND negative amount."""
        fields = _fields(
            total="-100",
        )
        rules = create_invoice_validation_rules()
        engine = ValidationEngine(rules=rules)
        result = engine.validate(
            "doc-1", "invoice", fields
        )
        assert result.status == ValidationStatus.INVALID
        assert len(result.errors) >= 2

    def test_is_valid_property(self):
        fields = _fields(
            invoice_number="INV-001",
            invoice_date="2026-09-01",
            subtotal="100",
            total="100",
        )
        rules = create_invoice_validation_rules()
        engine = ValidationEngine(rules=rules)
        result = engine.validate(
            "doc-1", "invoice", fields
        )
        assert result.is_valid


# ====================================================
# RuleResult serialization
# ====================================================

class TestRuleResultSerialization:

    def test_to_dict(self):
        result = RuleResult(
            rule_code="TOTAL_MISMATCH",
            status=RuleStatus.FAIL,
            message="Mismatch",
            expected_value="118",
            actual_value="120",
        )
        d = result.to_dict()
        assert d["rule_code"] == "TOTAL_MISMATCH"
        assert d["status"] == "FAIL"
        assert d["expected_value"] == "118"
        assert d["actual_value"] == "120"

    def test_to_dict_none_values(self):
        result = RuleResult(
            rule_code="TEST",
            status=RuleStatus.PASS,
        )
        d = result.to_dict()
        assert d["expected_value"] is None
        assert d["actual_value"] is None


# ====================================================
# ValidationResult
# ====================================================

class TestValidationResult:

    def test_errors_property(self):
        result = ValidationResult(
            results=[
                RuleResult("A", RuleStatus.PASS),
                RuleResult("B", RuleStatus.FAIL),
                RuleResult("C", RuleStatus.FAIL),
                RuleResult("D", RuleStatus.WARN),
            ]
        )
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

    def test_to_dict(self):
        result = ValidationResult(
            document_id="doc-1",
            document_type="invoice",
            status=ValidationStatus.VALID,
        )
        d = result.to_dict()
        assert d["document_id"] == "doc-1"
        assert d["status"] == "VALID"


# ====================================================
# Factory function
# ====================================================

class TestCreateInvoiceRules:

    def test_default_rules(self):
        rules = create_invoice_validation_rules()
        assert len(rules) == 6

    def test_rule_codes(self):
        rules = create_invoice_validation_rules()
        codes = [r.rule_code for r in rules]
        assert "REQUIRED_FIELDS" in codes
        assert "TOTAL_MISMATCH" in codes
        assert "DATE_INCONSISTENCY" in codes
        assert "INVALID_NUMERIC" in codes
        assert "NEGATIVE_AMOUNT" in codes
        assert "DUPLICATE_INVOICE_NUMBER" in codes

    def test_custom_tolerance(self):
        rules = create_invoice_validation_rules(
            tolerance=Decimal("1.00")
        )
        # Find the total rule and verify
        total_rule = [
            r for r in rules
            if r.rule_code == "TOTAL_MISMATCH"
        ][0]
        assert total_rule.tolerance == Decimal("1.00")
