"""
TF-IDF + cosine similarity engine.

Initial implementation of the SimilarityEngine
interface. Uses scikit-learn's TfidfVectorizer
for vectorization and cosine_similarity for
scoring.

Performance note:
- Batch mode vectorizes all texts together for
  efficiency (single TF-IDF fit + transform).
- Future upgrade path: replace with sentence-
  transformer embeddings + FAISS index.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

from sklearn.feature_extraction.text import (
    TfidfVectorizer,
)
from sklearn.metrics.pairwise import (
    cosine_similarity,
)

from app.dedup.base import SimilarityEngine


logger = logging.getLogger(__name__)


class TfidfSimilarityEngine(SimilarityEngine):
    """TF-IDF + cosine similarity engine.

    Computes document similarity by converting
    texts into TF-IDF vectors and measuring
    cosine distance.

    Attributes:
        max_features: Max vocabulary size for
            TF-IDF vectorizer.
        ngram_range: N-gram range for features.
    """

    def __init__(
        self,
        max_features: int = 10000,
        ngram_range: tuple[int, int] = (1, 2),
    ):

        self.max_features = max_features
        self.ngram_range = ngram_range

    def compute_similarity(
        self,
        text_a: str,
        text_b: str,
    ) -> float:
        """Compute cosine similarity between
        two texts.

        Returns 1.0 for identical texts, 0.0 for
        completely different texts.
        """

        if not text_a.strip() or not text_b.strip():
            return 0.0

        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(
                [text_a, text_b]
            )
        except ValueError:
            # Empty vocabulary
            return 0.0

        similarity = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:2],
        )

        return float(similarity[0][0])

    def compute_similarities_batch(
        self,
        query_text: str,
        candidate_texts: list[str],
    ) -> list[float]:
        """Compute similarity of query against
        all candidates in a single TF-IDF fit.

        More efficient than pairwise calls because
        the vocabulary is shared.
        """

        if not query_text.strip():
            return [0.0] * len(candidate_texts)

        if not candidate_texts:
            return []

        # Combine query + candidates for joint
        # vectorization
        all_texts = [query_text] + candidate_texts

        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(
                all_texts
            )
        except ValueError:
            return [0.0] * len(candidate_texts)

        # Query is index 0, candidates are 1..N
        similarities = cosine_similarity(
            tfidf_matrix[0:1],
            tfidf_matrix[1:],
        )

        return [
            float(s)
            for s in similarities[0]
        ]


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text
    for exact duplicate detection.

    Normalizes whitespace before hashing so that
    formatting differences don't affect the hash.

    Args:
        text: Document text.

    Returns:
        Hex digest string.
    """

    normalized = " ".join(text.split()).strip().lower()

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()
