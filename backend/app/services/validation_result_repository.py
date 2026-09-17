"""
Validation result repository.

CRUD operations for the validation_results table.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.validation_result import (
    ValidationResultModel,
)


logger = logging.getLogger(__name__)


class ValidationResultRepository:

    def __init__(self, session: Session):

        self.session = session

    def save(
        self,
        document_id: str,
        document_type: str,
        status: str,
        rule_results: list[dict],
    ) -> ValidationResultModel:
        """Save or update a validation result.

        Upsert pattern — updates if exists.

        Args:
            document_id: The document ID.
            document_type: Classified type.
            status: Overall VALID/INVALID/SKIPPED.
            rule_results: List of rule result dicts.

        Returns:
            The saved ValidationResultModel.
        """

        existing = self.get_by_document_id(
            document_id
        )

        if existing:

            existing.document_type = document_type
            existing.status = status
            existing.rule_results = rule_results
            existing.validated_at = (
                datetime.utcnow()
            )

            self.session.commit()
            self.session.refresh(existing)

            return existing

        result = ValidationResultModel(
            document_id=document_id,
            document_type=document_type,
            status=status,
            rule_results=rule_results,
            validated_at=datetime.utcnow(),
        )

        self.session.add(result)
        self.session.commit()
        self.session.refresh(result)

        return result

    def get_by_document_id(
        self, document_id: str
    ) -> Optional[ValidationResultModel]:
        """Get validation result for a document.

        Args:
            document_id: The document ID.

        Returns:
            ValidationResultModel or None.
        """

        statement = select(
            ValidationResultModel
        ).where(
            ValidationResultModel.document_id
            == document_id
        )

        return self.session.scalar(statement)
