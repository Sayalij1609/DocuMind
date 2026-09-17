"""
Duplicate detection service.

Orchestrates duplicate checking for a document:
1. Fetches the document's cleaned text
2. Fetches candidate documents (same type, completed)
3. Checks exact duplicates via content hash
4. Checks near duplicates via TF-IDF similarity
5. Persists results

Performance:
- Filters candidates by document_type first
- Uses batch similarity for efficiency
- Designed so future vector indexes (FAISS,
  Annoy) can replace brute-force comparison
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dedup.base import (
    DuplicateCheckResult,
    DuplicateMatch,
    DuplicateType,
    SimilarityEngine,
)
from app.dedup.tfidf_engine import (
    TfidfSimilarityEngine,
    compute_content_hash,
)
from app.models.document import (
    Document,
    DocumentStatus,
)
from app.models.document_content import (
    DocumentContent,
)


logger = logging.getLogger(__name__)


class DuplicateDetectionService:
    """Service for detecting duplicate documents.

    Separates exact duplicates (content hash) from
    near duplicates (TF-IDF cosine similarity).

    Attributes:
        session: SQLAlchemy session.
        engine: Similarity engine (pluggable).
        exact_threshold: Content-hash match is
            always exact (1.0). This is for
            the cosine score above which we still
            call it "exact" (default: 0.99).
        near_threshold: Minimum cosine similarity
            to consider a near duplicate
            (default: 0.85).
        max_candidates: Maximum number of candidate
            documents to compare against
            (performance guard).
    """

    def __init__(
        self,
        session: Session,
        engine: SimilarityEngine | None = None,
        exact_threshold: float = 0.99,
        near_threshold: float = 0.85,
        max_candidates: int = 500,
    ):

        self.session = session
        self.engine = (
            engine or TfidfSimilarityEngine()
        )
        self.exact_threshold = exact_threshold
        self.near_threshold = near_threshold
        self.max_candidates = max_candidates

    def check_document(
        self,
        document_id: str,
    ) -> DuplicateCheckResult:
        """Check a document for duplicates.

        1. Fetch the document's cleaned text
        2. Fetch candidates (same type, completed,
           excluding self)
        3. Content-hash check for exact duplicates
        4. TF-IDF batch comparison for near dupes
        5. Return matches above threshold

        Args:
            document_id: The document to check.

        Returns:
            DuplicateCheckResult with matches.
        """

        # Get source document text
        source_text = self._get_cleaned_text(
            document_id
        )

        if not source_text or not source_text.strip():

            logger.debug(
                "No text for document %s, "
                "skipping duplicate check.",
                document_id,
            )

            return DuplicateCheckResult(
                document_id=document_id,
                matches=[],
            )

        # Get source document type for filtering
        source_doc = self._get_document(
            document_id
        )

        document_type = (
            source_doc.document_type
            if source_doc
            else None
        )

        # Fetch candidates
        candidates = self._fetch_candidates(
            document_id=document_id,
            document_type=document_type,
        )

        if not candidates:

            return DuplicateCheckResult(
                document_id=document_id,
                matches=[],
                candidates_checked=0,
            )

        # Content hash for exact duplicates
        source_hash = compute_content_hash(
            source_text
        )

        matches: list[DuplicateMatch] = []
        candidate_ids: list[str] = []
        candidate_texts: list[str] = []

        now = datetime.now(timezone.utc)

        for cand_id, cand_text in candidates:

            cand_hash = compute_content_hash(
                cand_text
            )

            if source_hash == cand_hash:

                matches.append(
                    DuplicateMatch(
                        document_id=document_id,
                        matched_document_id=cand_id,
                        similarity_score=1.0,
                        duplicate_type=(
                            DuplicateType.EXACT
                        ),
                        detected_at=now,
                    )
                )

            else:
                # Queue for TF-IDF comparison
                candidate_ids.append(cand_id)
                candidate_texts.append(cand_text)

        # Batch TF-IDF comparison for remaining
        if candidate_texts:

            scores = (
                self.engine
                .compute_similarities_batch(
                    source_text, candidate_texts
                )
            )

            for cand_id, score in zip(
                candidate_ids, scores
            ):

                if score >= self.exact_threshold:

                    matches.append(
                        DuplicateMatch(
                            document_id=(
                                document_id
                            ),
                            matched_document_id=(
                                cand_id
                            ),
                            similarity_score=score,
                            duplicate_type=(
                                DuplicateType.EXACT
                            ),
                            detected_at=now,
                        )
                    )

                elif score >= self.near_threshold:

                    matches.append(
                        DuplicateMatch(
                            document_id=(
                                document_id
                            ),
                            matched_document_id=(
                                cand_id
                            ),
                            similarity_score=score,
                            duplicate_type=(
                                DuplicateType.NEAR
                            ),
                            detected_at=now,
                        )
                    )

        # Sort by similarity descending
        matches.sort(
            key=lambda m: m.similarity_score,
            reverse=True,
        )

        total_candidates = (
            len(matches)
            + len(candidate_texts)
        )

        logger.info(
            "Duplicate check for %s: "
            "%d candidates, %d matches "
            "(%d exact, %d near)",
            document_id,
            total_candidates,
            len(matches),
            sum(
                1 for m in matches
                if m.duplicate_type
                == DuplicateType.EXACT
            ),
            sum(
                1 for m in matches
                if m.duplicate_type
                == DuplicateType.NEAR
            ),
        )

        return DuplicateCheckResult(
            document_id=document_id,
            matches=matches,
            candidates_checked=total_candidates,
        )

    def _get_cleaned_text(
        self, document_id: str
    ) -> str | None:
        """Fetch cleaned text for a document."""

        stmt = (
            select(DocumentContent.cleaned_text)
            .where(
                DocumentContent.document_id
                == document_id
            )
        )

        return self.session.scalar(stmt)

    def _get_document(
        self, document_id: str
    ) -> Document | None:
        """Fetch document model."""

        stmt = (
            select(Document)
            .where(
                Document.document_id == document_id
            )
        )

        return self.session.scalar(stmt)

    def _fetch_candidates(
        self,
        document_id: str,
        document_type: str | None = None,
    ) -> list[tuple[str, str]]:
        """Fetch candidate documents for comparison.

        Filters:
        - Completed status only
        - Same document_type (if available)
        - Excludes self
        - Limited to max_candidates

        Returns:
            List of (document_id, cleaned_text) tuples.
        """

        stmt = (
            select(
                DocumentContent.document_id,
                DocumentContent.cleaned_text,
            )
            .join(
                Document,
                Document.document_id
                == DocumentContent.document_id,
            )
            .where(
                Document.status
                == DocumentStatus.COMPLETED,
                DocumentContent.document_id
                != document_id,
                DocumentContent.cleaned_text != "",
            )
        )

        if document_type:
            stmt = stmt.where(
                Document.document_type
                == document_type
            )

        stmt = stmt.limit(self.max_candidates)

        rows = self.session.execute(stmt).all()

        return [
            (row[0], row[1])
            for row in rows
        ]
