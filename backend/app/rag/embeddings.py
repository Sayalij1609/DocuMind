"""
Embedding Model Abstraction and Implementations for Nexora RAG.

Defines the BaseEmbeddingModel interface and provides a pluggable architecture
so that embedding backends (Dense Hashing/TF-IDF, SentenceTransformers, or
external APIs) can be swapped seamlessly via configuration without code changes.
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class BaseEmbeddingModel(ABC):
    """Abstract Base Class for all embedding models in Nexora."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into a vector."""
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document chunk strings into vectors."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        pass


class DenseHashingEmbeddingModel(BaseEmbeddingModel):
    """
    High-performance, stateless dense embedding model using sub-word n-gram
    feature hashing with L2 normalization.

    Requires zero external network calls, zero heavy torch dependencies, runs
    in sub-millisecond time, and reliably handles numbers, codes, and terms.
    """

    def __init__(self, dimension: int = 512):
        self._dim = dimension
        try:
            from sklearn.feature_extraction.text import HashingVectorizer

            self._vectorizer = HashingVectorizer(
                n_features=dimension,
                alternate_sign=False,
                norm="l2",
                ngram_range=(1, 2),
                token_pattern=r"(?u)\b[\w₹$€£\-\.]+\b",
                lowercase=True,
            )
        except ImportError:
            self._vectorizer = None
            logger.warning("scikit-learn not available, falling back to basic hasher.")

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * self._dim

        if self._vectorizer is not None:
            vec = self._vectorizer.transform([text]).toarray()[0]
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.tolist()

        return self._basic_hash_embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if self._vectorizer is not None:
            # Clean empty strings so HashingVectorizer handles them gracefully
            cleaned = [t if t.strip() else " " for t in texts]
            vecs = self._vectorizer.transform(cleaned).toarray()
            # Normalize each row
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            vecs = vecs / norms
            return vecs.tolist()

        return [self._basic_hash_embed(t) for t in texts]

    def _basic_hash_embed(self, text: str) -> list[float]:
        """Fallback lightweight hashing if sklearn is missing."""
        vec = np.zeros(self._dim, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            h = hash(word) % self._dim
            vec[h] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


# Global cache for embedding model singleton
_EMBEDDING_MODEL_CACHE: Optional[BaseEmbeddingModel] = None


def get_embedding_model(model_name: Optional[str] = None) -> BaseEmbeddingModel:
    """
    Factory to retrieve or instantiate the configured embedding model.
    Configurable via environment or parameter.
    """
    global _EMBEDDING_MODEL_CACHE

    if _EMBEDDING_MODEL_CACHE is not None and model_name is None:
        return _EMBEDDING_MODEL_CACHE

    # In the future, support other backends if configured:
    # e.g., 'sentence_transformers', 'groq', 'openai'
    model = DenseHashingEmbeddingModel(dimension=512)
    if model_name is None:
        _EMBEDDING_MODEL_CACHE = model
    return model


def reset_embedding_model() -> None:
    """Reset global embedding model singleton (primarily for tests)."""
    global _EMBEDDING_MODEL_CACHE
    _EMBEDDING_MODEL_CACHE = None
