"""
Vector Database / Vector Store for Nexora RAG.

Provides the BaseVectorStore interface and an optimized PersistentVectorStore
with cosine similarity indexing, persistent local disk serialization, and fast
metadata filtering (by document_id, document_ids, document_type).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional
import numpy as np

from app.rag.chunking import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class ScoredChunk:
    """A retrieved document chunk annotated with its similarity score."""

    chunk: DocumentChunk
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "score": round(float(self.score), 4),
        }


class BaseVectorStore(ABC):
    """Abstract interface for vector stores in Nexora."""

    @abstractmethod
    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Index a batch of chunks along with their vector embeddings."""
        pass

    @abstractmethod
    def query(
        self,
        query_vector: list[float],
        top_k: int = 4,
        filter_dict: Optional[dict[str, Any]] = None,
        min_similarity: float = 0.05,
    ) -> list[ScoredChunk]:
        """Retrieve the top-k most similar chunks matching filter criteria."""
        pass

    @abstractmethod
    def delete_by_document_id(self, document_id: str) -> int:
        """Remove all indexed chunks belonging to a document."""
        pass

    @abstractmethod
    def get_by_document_id(self, document_id: str) -> list[DocumentChunk]:
        """Fetch all chunks belonging to a document."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return the total number of indexed chunks."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all indexed data."""
        pass


class PersistentVectorStore(BaseVectorStore):
    """
    High-performance in-memory vector index with persistent local disk storage.
    Uses NumPy for vectorized cosine similarity search and metadata filtering.
    """

    def __init__(
        self,
        storage_path: Optional[str] = "storage/vector_store/index.json",
    ):
        self.storage_path = Path(storage_path) if storage_path else None
        self._chunks: list[DocumentChunk] = []
        self._chunk_map: dict[str, int] = {}  # chunk_id -> index
        self._embeddings: Optional[np.ndarray] = None  # shape: (N, D)
        self._load()

    def _load(self) -> None:
        """Load stored chunks and embeddings from disk if file exists."""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_chunks = data.get("chunks", [])
            raw_embeddings = data.get("embeddings", [])

            self._chunks = [DocumentChunk.from_dict(c) for c in raw_chunks]
            self._chunk_map = {c.chunk_id: idx for idx, c in enumerate(self._chunks)}

            if raw_embeddings and len(raw_embeddings) == len(self._chunks):
                self._embeddings = np.array(raw_embeddings, dtype=np.float32)
            else:
                self._embeddings = None

            logger.info(
                "Loaded %d chunks into PersistentVectorStore from %s",
                len(self._chunks),
                self.storage_path,
            )
        except Exception:
            logger.exception("Failed to load vector store from %s", self.storage_path)

    def _save(self) -> None:
        """Persist chunks and embeddings to disk."""
        if not self.storage_path:
            return

        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "chunks": [c.to_dict() for c in self._chunks],
                "embeddings": (
                    self._embeddings.tolist()
                    if self._embeddings is not None
                    else []
                ),
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            logger.exception("Failed to save vector store to %s", self.storage_path)

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Add or update chunks and their embeddings."""
        if not chunks:
            return

        emb_matrix = np.array(embeddings, dtype=np.float32)

        # Normalize incoming embeddings
        norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        emb_matrix = emb_matrix / norms

        for idx, chunk in enumerate(chunks):
            chunk_emb = emb_matrix[idx : idx + 1]

            if chunk.chunk_id in self._chunk_map:
                # Update existing chunk
                pos = self._chunk_map[chunk.chunk_id]
                self._chunks[pos] = chunk
                if self._embeddings is not None and pos < len(self._embeddings):
                    self._embeddings[pos] = chunk_emb[0]
            else:
                # Append new chunk
                pos = len(self._chunks)
                self._chunks.append(chunk)
                self._chunk_map[chunk.chunk_id] = pos

                if self._embeddings is None:
                    self._embeddings = chunk_emb
                else:
                    self._embeddings = np.vstack([self._embeddings, chunk_emb])

        self._save()
        logger.debug("Vector store now contains %d chunks", len(self._chunks))

    def query(
        self,
        query_vector: list[float],
        top_k: int = 4,
        filter_dict: Optional[dict[str, Any]] = None,
        min_similarity: float = 0.05,
    ) -> list[ScoredChunk]:
        """
        Cosine similarity search with optional metadata filtering.

        Supported filter keys:
          - document_id: exact match str
          - document_ids: list of str
          - document_type: exact match str
          - chunk_type: exact match str
        """
        if not self._chunks or self._embeddings is None or len(self._embeddings) == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm
        else:
            return []

        # 1. Identify candidate indices based on metadata filter
        candidate_indices: list[int] = []
        filter_doc_id = filter_dict.get("document_id") if filter_dict else None
        filter_doc_ids = filter_dict.get("document_ids") if filter_dict else None
        filter_doc_type = filter_dict.get("document_type") if filter_dict else None

        for idx, chunk in enumerate(self._chunks):
            if filter_doc_id and chunk.document_id != filter_doc_id:
                continue
            if filter_doc_ids and chunk.document_id not in filter_doc_ids:
                continue
            if filter_doc_type and chunk.document_type != filter_doc_type:
                continue
            candidate_indices.append(idx)

        if not candidate_indices:
            return []

        # 2. Compute similarity for candidate subset
        candidate_embs = self._embeddings[candidate_indices]
        scores = np.dot(candidate_embs, q_vec)

        # 3. Rank and filter by minimum similarity
        scored_pairs = []
        for i, cand_idx in enumerate(candidate_indices):
            score = float(scores[i])
            if score >= min_similarity:
                scored_pairs.append((cand_idx, score))

        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        top_pairs = scored_pairs[:top_k]

        return [
            ScoredChunk(chunk=self._chunks[idx], score=score)
            for idx, score in top_pairs
        ]

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks for a given document_id and rebuild vectors."""
        kept_chunks: list[DocumentChunk] = []
        kept_indices: list[int] = []
        deleted_count = 0

        for idx, c in enumerate(self._chunks):
            if c.document_id == document_id:
                deleted_count += 1
            else:
                kept_chunks.append(c)
                kept_indices.append(idx)

        if deleted_count > 0:
            self._chunks = kept_chunks
            self._chunk_map = {c.chunk_id: i for i, c in enumerate(kept_chunks)}
            if self._embeddings is not None and kept_indices:
                self._embeddings = self._embeddings[kept_indices]
            else:
                self._embeddings = None
            self._save()
            logger.info("Deleted %d chunks for document %s", deleted_count, document_id)

        return deleted_count

    def get_by_document_id(self, document_id: str) -> list[DocumentChunk]:
        return [c for c in self._chunks if c.document_id == document_id]

    def count(self) -> int:
        return len(self._chunks)

    def clear(self) -> None:
        self._chunks = []
        self._chunk_map = {}
        self._embeddings = None
        self._save()


# Global vector store singleton
_VECTOR_STORE_CACHE: Optional[PersistentVectorStore] = None


def get_vector_store() -> PersistentVectorStore:
    """Retrieve global PersistentVectorStore singleton."""
    global _VECTOR_STORE_CACHE
    if _VECTOR_STORE_CACHE is None:
        _VECTOR_STORE_CACHE = PersistentVectorStore()
    return _VECTOR_STORE_CACHE


def reset_vector_store() -> None:
    """Reset global vector store singleton (primarily for tests)."""
    global _VECTOR_STORE_CACHE
    _VECTOR_STORE_CACHE = None
