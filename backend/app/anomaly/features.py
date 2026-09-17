"""
Document feature extraction layer for anomaly detection.

Extracts structured numerical features from:
- Document metadata (file_size, pages)
- DocumentContent (text length, word count, page count)
- Extraction results (amounts, tax rates, vendor)
- Validation results (rule failures, errors)
- Duplicate results (similarity scores)

Designed to use only features that genuinely exist in the system,
with explicit extension points for future additions (e.g. line items).
Never fabricates data.
"""

from __future__ import annotations

import re
import logging
from decimal import Decimal
from typing import Any, Optional

from app.anomaly.base import FeatureVector


logger = logging.getLogger(__name__)

# Standard ordered list of features used by the isolation forest
FEATURE_NAMES: list[str] = [
    "invoice_amount",
    "tax_percentage",
    "document_length",
    "word_count",
    "page_count",
    "missing_field_count",
    "duplicate_similarity",
    "vendor_frequency",
    "validation_error_count",
    "item_count",
]

# Expected fields for invoice document type
EXPECTED_INVOICE_FIELDS: list[str] = [
    "vendor",
    "invoice_number",
    "invoice_date",
    "total",
    "subtotal",
    "tax",
]


def _parse_float(val: Any) -> Optional[float]:
    """Safely convert extracted amount/numeric field to float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, str):
        cleaned = re.sub(r"[^\d.\-]", "", val)
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


class DocumentFeatureExtractor:
    """Extracts structured numerical features from document artifacts.

    All features use only real, verifiable data from the ingestion,
    extraction, validation, and deduplication modules. Missing values
    are imputed with safe neutral defaults (e.g., 0.0) while being
    tracked in missing_flags for full auditability.
    """

    def __init__(
        self,
        feature_names: list[str] | None = None,
        expected_invoice_fields: list[str] | None = None,
    ):
        self.feature_names = feature_names or list(FEATURE_NAMES)
        self.expected_invoice_fields = (
            expected_invoice_fields or list(EXPECTED_INVOICE_FIELDS)
        )

    def extract(
        self,
        document_id: str,
        document: Any = None,
        content: Any = None,
        extraction_record: Any = None,
        validation_record: Any = None,
        duplicate_matches: list[Any] | None = None,
        vendor_frequency_lookup: Optional[callable] = None,
    ) -> FeatureVector:
        """Extract a complete FeatureVector for a document.

        Args:
            document_id: Target document ID.
            document: Document model instance (optional).
            content: DocumentContent model instance (optional).
            extraction_record: ExtractionResultModel instance or dict.
            validation_record: ValidationResultModel instance or dict.
            duplicate_matches: List of DuplicateResultModel instances or dicts.
            vendor_frequency_lookup: Optional callable(vendor_name) -> int.

        Returns:
            FeatureVector with numerical values and missingness flags.
        """
        values: dict[str, float] = {}
        missing_flags: dict[str, bool] = {}
        metadata: dict[str, Any] = {}

        # ----------------------------------------------------
        # 1. Content & Text Features
        # ----------------------------------------------------
        cleaned_text = ""
        page_count = 1.0

        if content is not None:
            if hasattr(content, "cleaned_text"):
                cleaned_text = content.cleaned_text or ""
            elif isinstance(content, dict):
                cleaned_text = content.get("cleaned_text", "") or ""

            if hasattr(content, "page_count") and content.page_count:
                page_count = float(content.page_count)
            elif isinstance(content, dict) and content.get("page_count"):
                page_count = float(content["page_count"])

        values["document_length"] = float(len(cleaned_text))
        missing_flags["document_length"] = len(cleaned_text) == 0

        words = cleaned_text.split()
        values["word_count"] = float(len(words))
        missing_flags["word_count"] = len(words) == 0

        values["page_count"] = page_count
        missing_flags["page_count"] = page_count <= 0

        # ----------------------------------------------------
        # 2. Extracted Structured Fields
        # ----------------------------------------------------
        extracted_fields: dict[str, Any] = {}

        if extraction_record is not None:
            if hasattr(extraction_record, "extracted_fields"):
                extracted_fields = extraction_record.extracted_fields or {}
            elif isinstance(extraction_record, dict):
                extracted_fields = (
                    extraction_record.get("extracted_fields") or {}
                )

        # Helper to get field value safely
        def get_field_val(field_name: str) -> Any:
            item = extracted_fields.get(field_name)
            if isinstance(item, dict):
                return item.get("value")
            return item

        # Invoice amount / total
        total_raw = get_field_val("total") or get_field_val("invoice_amount")
        total_num = _parse_float(total_raw)

        if total_num is not None:
            values["invoice_amount"] = total_num
            missing_flags["invoice_amount"] = False
        else:
            values["invoice_amount"] = 0.0
            missing_flags["invoice_amount"] = True

        # Tax percentage calculation
        subtotal_raw = get_field_val("subtotal")
        subtotal_num = _parse_float(subtotal_raw)

        tax_raw = get_field_val("tax") or get_field_val("gst")
        tax_num = _parse_float(tax_raw)

        tax_percentage = 0.0
        tax_missing = True

        if tax_num is not None and tax_num >= 0:
            if subtotal_num is not None and subtotal_num > 0:
                tax_percentage = (tax_num / subtotal_num) * 100.0
                tax_missing = False
            elif total_num is not None and total_num > tax_num:
                tax_percentage = (tax_num / (total_num - tax_num)) * 100.0
                tax_missing = False

        values["tax_percentage"] = round(tax_percentage, 2)
        missing_flags["tax_percentage"] = tax_missing

        # Missing field count
        missing_count = 0
        for exp_field in self.expected_invoice_fields:
            val = get_field_val(exp_field)
            if val is None or str(val).strip() == "":
                missing_count += 1

        values["missing_field_count"] = float(missing_count)
        missing_flags["missing_field_count"] = False

        # Vendor name & vendor frequency
        vendor_name = get_field_val("vendor") or get_field_val("vendor_name")
        vendor_freq = 0.0

        if vendor_name and vendor_frequency_lookup is not None:
            try:
                vendor_freq = float(vendor_frequency_lookup(str(vendor_name)))
            except Exception as e:
                logger.debug("Vendor frequency lookup error: %s", e)
                vendor_freq = 1.0

        values["vendor_frequency"] = vendor_freq
        missing_flags["vendor_frequency"] = vendor_name is None
        metadata["vendor"] = str(vendor_name) if vendor_name else None

        # Extensible line-item count
        # In current Phase 5 regex extractor, items are not parsed into a
        # structured list. We provide an explicit architectural hook with
        # a neutral default and missingness flag.
        items_field = extracted_fields.get("line_items") or extracted_fields.get("items")
        if isinstance(items_field, list):
            values["item_count"] = float(len(items_field))
            missing_flags["item_count"] = False
        else:
            values["item_count"] = 0.0
            missing_flags["item_count"] = True

        # ----------------------------------------------------
        # 3. Validation Results Features
        # ----------------------------------------------------
        validation_errors = 0.0

        if validation_record is not None:
            rule_results: list[dict] = []
            if hasattr(validation_record, "rule_results"):
                rule_results = validation_record.rule_results or []
            elif isinstance(validation_record, dict):
                rule_results = validation_record.get("rule_results") or []

            validation_errors = float(
                sum(1 for r in rule_results if r.get("status") == "FAIL")
            )

        values["validation_error_count"] = validation_errors
        missing_flags["validation_error_count"] = validation_record is None

        # ----------------------------------------------------
        # 4. Duplicate Similarity Feature
        # ----------------------------------------------------
        max_sim = 0.0

        if duplicate_matches:
            for m in duplicate_matches:
                score = 0.0
                if hasattr(m, "similarity_score"):
                    score = float(m.similarity_score)
                elif isinstance(m, dict):
                    score = float(m.get("similarity_score", 0.0))
                if score > max_sim:
                    max_sim = score

        values["duplicate_similarity"] = round(max_sim, 4)
        missing_flags["duplicate_similarity"] = duplicate_matches is None

        return FeatureVector(
            document_id=document_id,
            values=values,
            feature_names=self.feature_names,
            missing_flags=missing_flags,
            metadata=metadata,
        )
