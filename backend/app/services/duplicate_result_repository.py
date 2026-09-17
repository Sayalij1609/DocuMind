"""
Duplicate result repository.

CRUD operations for the duplicate_results table.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from app.models.duplicate_result import (
    DuplicateResultModel,
)


logger = logging.getLogger(__name__)


class DuplicateResultRepository:

    def __init__(self, session: Session):

        self.session = session

    def save_matches(
        self,
        matches: list[dict],
    ) -> list[DuplicateResultModel]:
        """Save multiple duplicate match results.

        Skips pairs that already exist (upsert-safe).

        Args:
            matches: List of dicts with keys:
                document_id, matched_document_id,
                similarity_score, duplicate_type,
                detected_at.

        Returns:
            List of saved models.
        """

        saved: list[DuplicateResultModel] = []

        for match_data in matches:

            existing = self._get_pair(
                match_data["document_id"],
                match_data["matched_document_id"],
            )

            if existing:
                # Update score if higher
                if (
                    match_data["similarity_score"]
                    > existing.similarity_score
                ):
                    existing.similarity_score = (
                        match_data[
                            "similarity_score"
                        ]
                    )
                    existing.duplicate_type = (
                        match_data["duplicate_type"]
                    )

                saved.append(existing)
                continue

            result = DuplicateResultModel(
                document_id=(
                    match_data["document_id"]
                ),
                matched_document_id=(
                    match_data[
                        "matched_document_id"
                    ]
                ),
                similarity_score=(
                    match_data["similarity_score"]
                ),
                duplicate_type=(
                    match_data["duplicate_type"]
                ),
                detected_at=(
                    match_data.get("detected_at")
                    or datetime.utcnow()
                ),
            )

            self.session.add(result)
            saved.append(result)

        self.session.commit()

        return saved

    def get_by_document_id(
        self, document_id: str
    ) -> list[DuplicateResultModel]:
        """Get all duplicate matches involving
        a document (as source or target).

        Args:
            document_id: The document ID.

        Returns:
            List of DuplicateResultModel.
        """

        stmt = (
            select(DuplicateResultModel)
            .where(
                or_(
                    DuplicateResultModel.document_id
                    == document_id,
                    DuplicateResultModel
                    .matched_document_id
                    == document_id,
                )
            )
            .order_by(
                DuplicateResultModel
                .similarity_score.desc()
            )
        )

        return list(
            self.session.scalars(stmt).all()
        )

    def _get_pair(
        self,
        document_id: str,
        matched_document_id: str,
    ) -> Optional[DuplicateResultModel]:
        """Check if a pair already exists
        (in either direction)."""

        stmt = (
            select(DuplicateResultModel)
            .where(
                or_(
                    and_(
                        DuplicateResultModel
                        .document_id
                        == document_id,
                        DuplicateResultModel
                        .matched_document_id
                        == matched_document_id,
                    ),
                    and_(
                        DuplicateResultModel
                        .document_id
                        == matched_document_id,
                        DuplicateResultModel
                        .matched_document_id
                        == document_id,
                    ),
                )
            )
        )

        return self.session.scalar(stmt)
