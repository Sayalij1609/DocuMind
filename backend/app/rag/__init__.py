"""
RAG (Retrieval-Augmented Generation) Module for Nexora.

Provides page-aware document chunking, pluggable vector embeddings,
in-memory / persistent vector indexing with metadata filtering,
controlled grounding prompts, and source-attributed Q&A.
"""

from app.rag.chunking import DocumentChunk, PageAwareChunker
from app.rag.embeddings import BaseEmbeddingModel, get_embedding_model
from app.rag.vector_store import BaseVectorStore, PersistentVectorStore, get_vector_store
from app.rag.prompt import build_grounded_rag_prompt, GROUNDING_FALLBACK_TEXT
from app.rag.llm import RAGLLMClient, get_rag_llm_client
from app.rag.pipeline import RAGPipeline, get_rag_pipeline

__all__ = [
    "DocumentChunk",
    "PageAwareChunker",
    "BaseEmbeddingModel",
    "get_embedding_model",
    "BaseVectorStore",
    "PersistentVectorStore",
    "get_vector_store",
    "build_grounded_rag_prompt",
    "GROUNDING_FALLBACK_TEXT",
    "RAGLLMClient",
    "get_rag_llm_client",
    "RAGPipeline",
    "get_rag_pipeline",
]
