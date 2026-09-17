"""
Unit tests for Phase 5 — Information Extraction.

Tests:
- Normalizers (amounts, dates, currency)
- Invoice extractor (all fields)
- Edge cases (empty, malformed, missing)
- Extraction result serialization
- Registry
"""

import pytest
from decimal import Decimal

from app.ml.extraction.normalizers import (
    normalize_amount,
    normalize_date,
    normalize_currency_symbol,
)
from app.ml.extraction.base import (
    FieldResult,
    ExtractionResult,
)
from app.ml.extraction.invoice_extractor import (
    InvoiceExtractor,
)
from app.ml.extraction.registry import (
    ExtractionStrategyRegistry,
)


# ====================================================
# Amount normalization tests
# ====================================================

class TestNormalizeAmount:

    def test_plain_integer(self):
        assert normalize_amount("100890") == Decimal("100890")

    def test_comma_thousands(self):
        assert normalize_amount("100,890") == Decimal("100890")

    def test_rupee_symbol(self):
        assert normalize_amount("₹100,890") == Decimal("100890")

    def test_inr_prefix(self):
        assert normalize_amount("INR 100890") == Decimal("100890")

    def test_rupee_with_decimals(self):
        assert normalize_amount("₹ 100,890.00") == Decimal("100890.00")

    def test_dollar_sign(self):
        assert normalize_amount("$1,234.56") == Decimal("1234.56")

    def test_indian_style_grouping(self):
        assert normalize_amount("1,00,890.50") == Decimal("100890.50")

    def test_negative_amount(self):
        assert normalize_amount("-500.00") == Decimal("-500.00")

    def test_plain_decimal(self):
        assert normalize_amount("99.99") == Decimal("99.99")

    def test_empty_string(self):
        assert normalize_amount("") is None

    def test_none_like(self):
        assert normalize_amount("   ") is None

    def test_garbage(self):
        assert normalize_amount("abc xyz") is None

    def test_rs_prefix(self):
        assert normalize_amount("Rs. 5,000") == Decimal("5000")

    def test_euro_symbol(self):
        assert normalize_amount("€1,234.56") == Decimal("1234.56")

    def test_european_decimal_comma(self):
        # "100,50" with exactly 2 digits after comma
        # treated as decimal separator
        assert normalize_amount("100,50") == Decimal("100.50")


# ====================================================
# Date normalization tests
# ====================================================

class TestNormalizeDate:

    def test_iso_format(self):
        assert normalize_date("2026-09-07") == "2026-09-07"

    def test_dd_mm_yyyy_slash(self):
        assert normalize_date("07/09/2026") == "2026-09-07"

    def test_dd_mm_yyyy_dot(self):
        assert normalize_date("07.09.2026") == "2026-09-07"

    def test_dd_month_yyyy(self):
        assert normalize_date("07 September 2026") == "2026-09-07"

    def test_month_dd_yyyy(self):
        assert normalize_date("September 07, 2026") == "2026-09-07"

    def test_dd_mon_yyyy_dash(self):
        assert normalize_date("07-Sep-2026") == "2026-09-07"

    def test_dd_mon_yyyy_slash(self):
        assert normalize_date("07/Sep/2026") == "2026-09-07"

    def test_date_in_context(self):
        result = normalize_date(
            "Invoice Date: 07 September 2026"
        )
        assert result == "2026-09-07"

    def test_empty_string(self):
        assert normalize_date("") is None

    def test_none_like(self):
        assert normalize_date("   ") is None

    def test_garbage(self):
        assert normalize_date("not a date") is None

    def test_partial_date(self):
        # No year — should not parse
        assert normalize_date("07 Sep") is None


# ====================================================
# Currency symbol normalization tests
# ====================================================

class TestNormalizeCurrencySymbol:

    def test_rupee_symbol(self):
        assert normalize_currency_symbol("₹") == "INR"

    def test_inr_text(self):
        assert normalize_currency_symbol("INR") == "INR"

    def test_dollar_sign(self):
        assert normalize_currency_symbol("$") == "USD"

    def test_euro_sign(self):
        assert normalize_currency_symbol("€") == "EUR"

    def test_pound_sign(self):
        assert normalize_currency_symbol("£") == "GBP"

    def test_rs_text(self):
        assert normalize_currency_symbol("Rs.") == "INR"

    def test_empty(self):
        assert normalize_currency_symbol("") is None

    def test_unknown(self):
        assert normalize_currency_symbol("XYZ") is None

    def test_in_context(self):
        assert normalize_currency_symbol("₹100") == "INR"


# ====================================================
# Invoice extractor tests
# ====================================================

class TestInvoiceExtractor:

    @pytest.fixture
    def extractor(self):
        return InvoiceExtractor()

    # ---------- Invoice number ----------

    def test_invoice_number_standard(
        self, extractor
    ):
        text = "Invoice Number: INV-1024\nSome text"
        result = extractor.extract(text)
        field = result.fields["invoice_number"]
        assert field.value == "INV-1024"
        assert field.confidence >= 0.9
        assert field.source == "regex"

    def test_invoice_number_hash(
        self, extractor
    ):
        text = "Invoice # 98765\nOther content"
        result = extractor.extract(text)
        field = result.fields["invoice_number"]
        assert field.value == "98765"
        assert field.confidence >= 0.9

    def test_invoice_number_bill_no(
        self, extractor
    ):
        text = "Bill No: BL-2026-001\nDetails"
        result = extractor.extract(text)
        field = result.fields["invoice_number"]
        assert field.value == "BL-2026-001"

    def test_invoice_number_inv_prefix(
        self, extractor
    ):
        text = "Reference: INV-5678 for services"
        result = extractor.extract(text)
        field = result.fields["invoice_number"]
        assert "5678" in field.value

    def test_invoice_number_missing(
        self, extractor
    ):
        text = "Just a random document with no ID"
        result = extractor.extract(text)
        field = result.fields["invoice_number"]
        assert field.value is None
        assert field.confidence == 0.0

    # ---------- Vendor ----------

    def test_vendor_with_suffix(
        self, extractor
    ):
        text = (
            "Acme Corp Pvt Ltd\n"
            "Invoice Number: INV-001\n"
            "Total: ₹5,000"
        )
        result = extractor.extract(text)
        field = result.fields["vendor"]
        assert "Acme Corp Pvt Ltd" in field.value
        assert field.confidence >= 0.8
        assert field.source == "keyword_proximity"

    def test_vendor_llc(self, extractor):
        text = (
            "Global Solutions LLC\n"
            "123 Business Street\n"
            "Invoice No: 999"
        )
        result = extractor.extract(text)
        field = result.fields["vendor"]
        assert "Global Solutions LLC" in field.value

    def test_vendor_heuristic_fallback(
        self, extractor
    ):
        text = (
            "John Smith Consulting\n"
            "Invoice Number: 123\n"
            "Total: $500"
        )
        result = extractor.extract(text)
        field = result.fields["vendor"]
        # Should still find something via heuristic
        assert field.value is not None
        assert field.confidence > 0.0

    def test_vendor_empty_doc(self, extractor):
        text = ""
        result = extractor.extract(text)
        assert (
            result.fields.get("vendor") is None
            or result.fields["vendor"].value is None
        )

    # ---------- Dates ----------

    def test_invoice_date_standard(
        self, extractor
    ):
        text = (
            "Invoice Date: 07 September 2026\n"
            "Due Date: 07 October 2026"
        )
        result = extractor.extract(text)
        field = result.fields["invoice_date"]
        assert field.value == "2026-09-07"
        assert field.confidence >= 0.8

    def test_due_date_standard(self, extractor):
        text = (
            "Invoice Date: 07/09/2026\n"
            "Due Date: 07/10/2026"
        )
        result = extractor.extract(text)
        field = result.fields["due_date"]
        assert field.value == "2026-10-07"

    def test_date_missing(self, extractor):
        text = "Invoice Number: 123\nTotal: $500"
        result = extractor.extract(text)
        field = result.fields["invoice_date"]
        assert field.confidence == 0.0

    # ---------- Amounts ----------

    def test_total_extraction(self, extractor):
        text = (
            "Subtotal: ₹10,000\n"
            "Tax: ₹1,800\n"
            "Grand Total: ₹11,800"
        )
        result = extractor.extract(text)
        field = result.fields["total"]
        assert field.value is not None
        assert Decimal(field.value) == Decimal("11800")

    def test_subtotal_extraction(self, extractor):
        text = "Subtotal: $1,500.00\nTax: $150.00"
        result = extractor.extract(text)
        field = result.fields["subtotal"]
        assert field.value is not None
        assert Decimal(field.value) == Decimal("1500.00")

    def test_tax_extraction(self, extractor):
        text = "Tax Amount: ₹900\nTotal: ₹5,900"
        result = extractor.extract(text)
        field = result.fields["tax"]
        assert field.value is not None
        assert Decimal(field.value) == Decimal("900")

    def test_gst_extraction(self, extractor):
        text = "GST: ₹1,620\nTotal: ₹10,620"
        result = extractor.extract(text)
        field = result.fields["gst"]
        assert field.value is not None
        assert Decimal(field.value) == Decimal("1620")

    def test_amount_due(self, extractor):
        text = "Amount Due: $2,500.00"
        result = extractor.extract(text)
        field = result.fields["total"]
        assert field.value is not None
        assert Decimal(field.value) == Decimal("2500.00")

    def test_amount_missing(self, extractor):
        text = "This is just some random text."
        result = extractor.extract(text)
        field = result.fields["total"]
        assert field.value is None
        assert field.confidence == 0.0

    # ---------- Full document ----------

    def test_full_invoice_extraction(
        self, extractor
    ):
        text = (
            "Nexora Technologies Pvt Ltd\n"
            "123 Business Park, Mumbai\n"
            "\n"
            "TAX INVOICE\n"
            "\n"
            "Invoice Number: INV-2026-0042\n"
            "Invoice Date: 07 September 2026\n"
            "Due Date: 07 October 2026\n"
            "\n"
            "Description    Qty    Rate    Amount\n"
            "Web Dev        1      80000   80000\n"
            "Cloud          1      10000   10000\n"
            "\n"
            "Subtotal: ₹90,000\n"
            "GST (18%): ₹16,200\n"
            "Grand Total: ₹1,06,200\n"
        )
        result = extractor.extract(text)

        assert result.document_type == "invoice"
        assert result.extraction_method == "regex_v1"

        # Vendor
        vendor = result.fields["vendor"]
        assert "Nexora Technologies" in vendor.value

        # Invoice number
        inv_num = result.fields["invoice_number"]
        assert inv_num.value == "INV-2026-0042"

        # Dates
        inv_date = result.fields["invoice_date"]
        assert inv_date.value == "2026-09-07"

        due_date = result.fields["due_date"]
        assert due_date.value == "2026-10-07"

        # Amounts
        subtotal = result.fields["subtotal"]
        assert subtotal.value is not None
        assert Decimal(subtotal.value) == Decimal("90000")

        gst = result.fields["gst"]
        assert gst.value is not None

        total = result.fields["total"]
        assert total.value is not None

    # ---------- Edge cases ----------

    def test_empty_document(self, extractor):
        result = extractor.extract("")
        assert result.document_type == "invoice"
        assert len(result.fields) == 0

    def test_whitespace_only(self, extractor):
        result = extractor.extract("   \n\n  ")
        assert len(result.fields) == 0

    def test_malformed_amounts(self, extractor):
        text = "Total: abc xyz\nSubtotal: ???"
        result = extractor.extract(text)
        # Should not crash, fields should have
        # low confidence
        assert result is not None

    def test_multiple_totals(self, extractor):
        text = (
            "Subtotal: ₹10,000\n"
            "Total Tax: ₹1,800\n"
            "Grand Total: ₹11,800\n"
            "Total Due: ₹11,800"
        )
        result = extractor.extract(text)
        total = result.fields["total"]
        # Should pick "Grand Total" (more specific)
        assert total.value is not None
        assert total.confidence > 0.0


# ====================================================
# ExtractionResult serialization tests
# ====================================================

class TestExtractionResult:

    def test_to_dict(self):
        result = ExtractionResult(
            document_type="invoice",
            fields={
                "total": FieldResult(
                    value="1000.00",
                    confidence=0.95,
                    source="regex",
                ),
            },
            extraction_method="regex_v1",
            version="1.0.0",
        )

        d = result.to_dict()

        assert d["document_type"] == "invoice"
        assert d["fields"]["total"]["value"] == "1000.00"
        assert d["fields"]["total"]["confidence"] == 0.95
        assert d["fields"]["total"]["source"] == "regex"
        assert d["fields"]["total"]["bbox"] is None

    def test_from_dict(self):
        data = {
            "document_type": "invoice",
            "extraction_method": "regex_v1",
            "version": "1.0.0",
            "fields": {
                "total": {
                    "value": "500",
                    "confidence": 0.9,
                    "source": "keyword_proximity",
                    "bbox": None,
                }
            },
        }

        result = ExtractionResult.from_dict(data)

        assert result.document_type == "invoice"
        assert result.fields["total"].value == "500"
        assert result.fields["total"].confidence == 0.9

    def test_roundtrip(self):
        original = ExtractionResult(
            document_type="invoice",
            fields={
                "vendor": FieldResult(
                    value="Acme Ltd",
                    confidence=0.85,
                    source="keyword_proximity",
                ),
                "total": FieldResult(
                    value="9999.99",
                    confidence=0.90,
                    source="regex",
                ),
            },
        )

        d = original.to_dict()
        restored = ExtractionResult.from_dict(d)

        assert (
            restored.fields["vendor"].value
            == "Acme Ltd"
        )
        assert (
            restored.fields["total"].value
            == "9999.99"
        )


# ====================================================
# Registry tests
# ====================================================

class TestExtractionRegistry:

    def test_invoice_registered(self):
        registry = ExtractionStrategyRegistry()
        extractor = registry.get("invoice")
        assert extractor is not None
        assert (
            extractor.supported_document_type
            == "invoice"
        )

    def test_unknown_type_returns_none(self):
        registry = ExtractionStrategyRegistry()
        assert registry.get("receipt") is None

    def test_supported_types(self):
        registry = ExtractionStrategyRegistry()
        assert "invoice" in registry.supported_types

    def test_custom_registration(self):
        from app.ml.extraction.base import (
            BaseExtractor,
        )

        class DummyExtractor(BaseExtractor):
            @property
            def supported_document_type(self):
                return "receipt"

            def extract(self, text, pages=None):
                return ExtractionResult(
                    document_type="receipt"
                )

        registry = ExtractionStrategyRegistry()
        registry.register(DummyExtractor())
        assert registry.get("receipt") is not None
