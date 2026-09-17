"""
Duplicate detection base classes.

Defines the abstract SimilarityEngine interface,
DuplicateType enum, and DuplicateMatch data
structure.

Architecture is pluggable: TF-IDF for now,
sentence-transformer embeddings later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DuplicateType(str, Enum):
    """Classification of duplicate relationship."""

    EXACT = "exact"
    NEAR = "near"


@dataclass
class DuplicateMatch:
    """A single duplicate match between two
    documents.

    Attributes:
        document_id: The source document.
        matched_document_id: The matched document.
        similarity_score: 0.0–1.0 cosine similarity.
        duplicate_type: EXACT or NEAR.
        detected_at: Timestamp.
    """

    document_id: str
    matched_document_id: str
    similarity_score: float
    duplicate_type: DuplicateType
    detected_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "matched_document_id": (
                self.matched_document_id
            ),
            "similarity_score": round(
                self.similarity_score, 4
            ),
            "duplicate_type": (
                self.duplicate_type.value
            ),
            "detected_at": (
                self.detected_at.isoformat()
                if self.detected_at
                else None
            ),
        }


@dataclass
class DuplicateCheckResult:
    """Result of checking a document for duplicates.

    Attributes:
        document_id: The checked document.
        matches: List of duplicate matches found.
        candidates_checked: How many documents
            were compared against.
    """

    document_id: str
    matches: list[DuplicateMatch]
    candidates_checked: int = 0

    @property
    def has_duplicates(self) -> bool:
        return len(self.matches) > 0

    @property
    def exact_matches(self) -> list[DuplicateMatch]:
        return [
            m for m in self.matches
            if m.duplicate_type == DuplicateType.EXACT
        ]

    @property
    def near_matches(self) -> list[DuplicateMatch]:
        return [
            m for m in self.matches
            if m.duplicate_type == DuplicateType.NEAR
        ]


class SimilarityEngine(ABC):
    """Abstract similarity engine.

    Pluggable backend for computing document
    similarity. TF-IDF is the initial implementation;
    sentence-transformer embeddings can replace it.
    """

    @abstractmethod
    def compute_similarity(
        self,
        text_a: str,
        text_b: str,
    ) -> float:
        """Compute similarity between two texts.

        Args:
            text_a: First document text.
            text_b: Second document text.

        Returns:
            Similarity score in [0.0, 1.0].
        """
        ...

    @abstractmethod
    def compute_similarities_batch(
        self,
        query_text: str,
        candidate_texts: list[str],
    ) -> list[float]:
        """Compute similarity of query against
        multiple candidates efficiently.

        Args:
            query_text: The query document text.
            candidate_texts: List of candidate texts.

        Returns:
            List of similarity scores, one per
            candidate.
        """
        ...
