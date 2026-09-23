"""
Validation service.

Orchestrates document validation:
1. Creates the appropriate validation engine
   for the document type
2. Runs all rules against extracted fields
3. Persists the result
"""

import logging
from typing import Optional

from app.validation.base import (
    ValidationEngine,
    ValidationResult,
)
from app.validation.rules import (
    create_invoice_validation_rules,
    create_bank_statement_validation_rules,
    create_salary_slip_validation_rules,
    create_utility_bill_validation_rules,
    create_receipt_validation_rules,
    create_general_financial_validation_rules,
)
from app.services.validation_result_repository import (
    ValidationResultRepository,
)


logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating extracted document
    fields using deterministic business rules.
    """

    def __init__(
        self,
        repository: ValidationResultRepository,
    ):

        self.repository = repository

    def validate_document(
        self,
        document_id: str,
        document_type: str,
        extracted_fields: dict,
    ) -> Optional[ValidationResult]:
        """Validate a document's extracted fields.

        Creates the appropriate rule set for the
        document type and runs validation.

        Args:
            document_id: The document ID.
            document_type: Classified type.
            extracted_fields: Extraction output
                (field name → {value, confidence, ...}).

        Returns:
            ValidationResult or None if no rules
            exist for this document type.
        """

        engine = self._create_engine(
            document_type
        )

        if engine is None:

            logger.debug(
                "No validation rules for "
                "document type '%s', skipping "
                "validation for %s",
                document_type,
                document_id,
            )

            return None

        result = engine.validate(
            document_id=document_id,
            document_type=document_type,
            extracted_fields=extracted_fields,
        )

        # Persist
        self.repository.save(
            document_id=document_id,
            document_type=result.document_type,
            status=result.status.value,
            rule_results=[
                r.to_dict() for r in result.results
            ],
        )

        logger.info(
            "Validation completed for document "
            "%s: %s (%d rules, %d errors)",
            document_id,
            result.status.value,
            len(result.results),
            len(result.errors),
        )

        return result

    def _create_engine(
        self,
        document_type: str,
    ) -> Optional[ValidationEngine]:
        """Create validation engine for a document type."""
        if document_type in ["invoice", "commercial_invoice", "tax_invoice"]:
            rules = create_invoice_validation_rules()
        elif document_type == "bank_statement":
            rules = create_bank_statement_validation_rules()
        elif document_type == "salary_slip":
            rules = create_salary_slip_validation_rules()
        elif document_type == "utility_bill":
            rules = create_utility_bill_validation_rules()
        elif document_type == "receipt":
            rules = create_receipt_validation_rules()
        else:
            rules = create_general_financial_validation_rules()

        return ValidationEngine(rules=rules)

