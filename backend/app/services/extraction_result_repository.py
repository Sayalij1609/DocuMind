"""
Extraction result repository.

CRUD operations for the extraction_results table.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.extraction_result import (
    ExtractionResultModel,
)


logger = logging.getLogger(__name__)


class ExtractionResultRepository:

    def __init__(self, session: Session):

        self.session = session

    @staticmethod
    def _extract_indexed_fields(
        extracted_fields: dict,
    ) -> tuple[Optional[str], Optional[str], Optional[float]]:
        """Extract indexed search columns from extracted_fields dictionary."""
        inv_no = None
        vendor = None
        total_amt = None

        if not isinstance(extracted_fields, dict):
            return inv_no, vendor, total_amt

        # 1. Invoice Number
        inv_data = (
            extracted_fields.get("invoice_number")
            or extracted_fields.get("invoice_id")
        )
        if isinstance(inv_data, dict):
            val = inv_data.get("value")
            inv_no = str(val) if val is not None else None
        elif inv_data is not None:
            inv_no = str(inv_data)

        # 2. Vendor
        vendor_data = (
            extracted_fields.get("vendor")
            or extracted_fields.get("vendor_name")
        )
        if isinstance(vendor_data, dict):
            val = vendor_data.get("value")
            vendor = str(val) if val is not None else None
        elif vendor_data is not None:
            vendor = str(vendor_data)

        # 3. Total Amount
        total_data = (
            extracted_fields.get("total_amount")
            or extracted_fields.get("amount")
            or extracted_fields.get("total")
        )
        raw_val = (
            total_data.get("value")
            if isinstance(total_data, dict)
            else total_data
        )
        if raw_val is not None:
            try:
                if isinstance(raw_val, str):
                    cleaned = (
                        raw_val.replace("$", "")
                        .replace("€", "")
                        .replace("£", "")
                        .replace(",", "")
                        .strip()
                    )
                    total_amt = float(cleaned)
                else:
                    total_amt = float(raw_val)
            except (ValueError, TypeError):
                total_amt = None

        return inv_no, vendor, total_amt

    def save(
        self,
        document_id: str,
        document_type: str,
        extracted_fields: dict,
        extraction_method: str,
        extraction_version: str,
    ) -> ExtractionResultModel:
        """Save or update an extraction result.

        If a result already exists for the document,
        it is updated (upsert pattern).

        Args:
            document_id: The document ID.
            document_type: Classified document type.
            extracted_fields: Dict of field results.
            extraction_method: Method identifier.
            extraction_version: Version string.

        Returns:
            The saved ExtractionResultModel.
        """
        inv_no, vendor, total_amt = self._extract_indexed_fields(
            extracted_fields
        )

        existing = self.get_by_document_id(
            document_id
        )

        if existing:

            existing.document_type = document_type
            existing.extracted_fields = (
                extracted_fields
            )
            existing.extraction_method = (
                extraction_method
            )
            existing.extraction_version = (
                extraction_version
            )
            existing.extracted_at = (
                datetime.utcnow()
            )
            existing.invoice_number = inv_no
            existing.vendor = vendor
            existing.total_amount = total_amt

            self.session.commit()
            self.session.refresh(existing)

            return existing

        result = ExtractionResultModel(
            document_id=document_id,
            document_type=document_type,
            invoice_number=inv_no,
            vendor=vendor,
            total_amount=total_amt,
            extracted_fields=extracted_fields,
            extraction_method=extraction_method,
            extraction_version=extraction_version,
            extracted_at=datetime.utcnow(),
        )

        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)

        return result

    def get_by_document_id(
        self, document_id: str
    ) -> Optional[ExtractionResultModel]:
        """Get extraction result for a document.

        Args:
            document_id: The document ID.

        Returns:
            ExtractionResultModel or None.
        """

        statement = select(
            ExtractionResultModel
        ).where(
            ExtractionResultModel.document_id
            == document_id
        )

        return self.session.scalar(statement)

    def search_by_invoice_number(
        self, invoice_number: str
    ) -> list[ExtractionResultModel]:
        """Search extraction results by exact invoice number."""
        statement = select(
            ExtractionResultModel
        ).where(
            ExtractionResultModel.invoice_number
            == invoice_number
        )
        return list(self.session.scalars(statement).all())

    def search_by_vendor(
        self, vendor: str
    ) -> list[ExtractionResultModel]:
        """Search extraction results by vendor name."""
        statement = select(
            ExtractionResultModel
        ).where(
            ExtractionResultModel.vendor
            == vendor
        )
        return list(self.session.scalars(statement).all())

