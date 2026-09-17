"""
Anomaly result repository.

CRUD operations for the anomaly_results table with upsert safety.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.anomaly.base import AnomalyResult
from app.models.anomaly_result import AnomalyResultModel


logger = logging.getLogger(__name__)


class AnomalyResultRepository:
    """Repository for managing AnomalyResultModel records."""

    def __init__(self, session: Session):
        self.session = session

    def save_result(
        self,
        result: AnomalyResult,
    ) -> AnomalyResultModel:
        """Save or update an anomaly detection result for a document.

        Upsert-safe: updates existing record if document_id already exists.

        Args:
            result: AnomalyResult instance.

        Returns:
            Saved or updated AnomalyResultModel.
        """
        existing = self.get_by_document_id(result.document_id)
        now = datetime.now(timezone.utc)

        if existing:
            existing.is_anomaly = result.is_anomaly
            existing.anomaly_score = result.anomaly_score
            existing.decision_function_score = (
                result.decision_function_score
            )
            existing.features = result.features
            existing.model_version = result.model_version
            existing.detected_at = result.detected_at or now
            existing.updated_at = now
            self.session.commit()
            return existing

        record = AnomalyResultModel(
            document_id=result.document_id,
            is_anomaly=result.is_anomaly,
            anomaly_score=result.anomaly_score,
            decision_function_score=(
                result.decision_function_score
            ),
            features=result.features,
            model_version=result.model_version,
            detected_at=result.detected_at or now,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def get_by_document_id(
        self,
        document_id: str,
    ) -> Optional[AnomalyResultModel]:
        """Fetch anomaly result for a given document.

        Args:
            document_id: Unique document identifier.

        Returns:
            AnomalyResultModel or None if not evaluated yet.
        """
        stmt = select(AnomalyResultModel).where(
            AnomalyResultModel.document_id == document_id
        )
        return self.session.scalar(stmt)

    def list_anomalies(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AnomalyResultModel]:
        """Fetch list of flagged anomalous documents.

        Args:
            limit: Page limit.
            offset: Page offset.

        Returns:
            List of AnomalyResultModel where is_anomaly == True,
            ordered by anomaly_score descending.
        """
        stmt = (
            select(AnomalyResultModel)
            .where(AnomalyResultModel.is_anomaly.is_(True))
            .order_by(AnomalyResultModel.anomaly_score.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())
