"""
End-to-End RAG Pipeline Orchestrator for Nexora.

Connects Document Chunking, Vector Embeddings, Vector Retrieval with Metadata
Filtering, Context Construction, and Grounded Question Answering with Citations.
"""

import logging
from typing import Any, Optional

from app.rag.chunking import DocumentChunk, PageAwareChunker
from app.rag.embeddings import BaseEmbeddingModel, get_embedding_model
from app.rag.llm import RAGLLMClient, get_rag_llm_client
from app.rag.prompt import GROUNDING_FALLBACK_TEXT, build_grounded_rag_prompt
from app.rag.vector_store import BaseVectorStore, ScoredChunk, get_vector_store

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Orchestrates indexing and retrieval-augmented generation."""

    def __init__(
        self,
        chunker: Optional[PageAwareChunker] = None,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        vector_store: Optional[BaseVectorStore] = None,
        llm_client: Optional[RAGLLMClient] = None,
    ):
        self.chunker = chunker or PageAwareChunker()
        self.embedding_model = embedding_model or get_embedding_model()
        self.vector_store = vector_store or get_vector_store()
        self.llm_client = llm_client or get_rag_llm_client()

    # ==========================================
    # Document Indexing
    # ==========================================

    def index_document(
        self,
        document_id: str,
        document_type: str = "unknown",
        filename: str = "",
        pages: Optional[list[Any]] = None,
        fallback_text: str = "",
        extraction_data: Optional[dict[str, Any]] = None,
    ) -> int:
        """
        Extract page chunks, compute vector embeddings, and index into vector store.
        Deletes any previous index for this document_id to guarantee idempotence.
        """
        # Remove any stale chunks for this document
        self.vector_store.delete_by_document_id(document_id)

        # Generate page-aware and structured entity chunks
        chunks = self.chunker.create_chunks(
            document_id=document_id,
            document_type=document_type,
            filename=filename,
            pages=pages,
            fallback_text=fallback_text,
            extraction_data=extraction_data,
        )

        if not chunks:
            logger.warning("No chunks generated for document: %s", document_id)
            return 0

        # Compute embeddings
        texts = [c.text for c in chunks]
        embeddings = self.embedding_model.embed_documents(texts)

        # Index in vector store
        self.vector_store.add_chunks(chunks, embeddings)
        logger.info(
            "Successfully indexed %d chunks for document: %s (%s)",
            len(chunks),
            document_id,
            filename,
        )
        return len(chunks)

    # ==========================================
    # Single Document Question Answering
    # ==========================================

    def query_document(
        self,
        document_id: str,
        question: str,
        document_type: Optional[str] = None,
        top_k: int = 4,
        min_similarity: float = 0.05,
    ) -> dict[str, Any]:
        """
        Execute RAG question-answering strictly scoped to a single document.
        Uses metadata filtering to ensure chunks from other documents never leak.
        """
        if not question or not question.strip():
            return {
                "answer": "Please provide a valid question.",
                "sources": [],
                "citations": [],
                "method": "input_validation",
            }

        clean_q = question.strip()

        # 1. Embed query
        q_emb = self.embedding_model.embed_query(clean_q)

        # 2. Vector retrieval filtered by document_id
        filter_dict = {"document_id": document_id}
        scored_chunks = self.vector_store.query(
            query_vector=q_emb,
            top_k=top_k,
            filter_dict=filter_dict,
            min_similarity=min_similarity,
        )

        # 3. Handle zero chunks found
        if not scored_chunks:
            return {
                "answer": GROUNDING_FALLBACK_TEXT,
                "sources": [],
                "citations": [],
                "method": "grounding_guardrail",
            }

        # 4. Construct grounded prompt
        system_prompt, user_prompt = build_grounded_rag_prompt(
            question=clean_q,
            scored_chunks=scored_chunks,
            document_type=document_type,
        )

        # 5. Generate answer via LLM (or deterministic fallback)
        llm_response = self.llm_client.generate_grounded_answer(
            question=clean_q,
            scored_chunks=scored_chunks,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # 6. Format structured source citations
        sources = self._build_source_citations(scored_chunks)
        citations = llm_response.get("citations", [])
        if not citations and sources and llm_response["answer"] != GROUNDING_FALLBACK_TEXT:
            top_src = sources[0]
            citations = [f"{top_src['filename'] or 'Document'} — Page {top_src['page_number']}"]

        return {
            "answer": llm_response["answer"],
            "sources": sources,
            "citations": citations,
            "method": llm_response.get("method", "rag"),
        }

    # ==========================================
    # Cross-Document Repository Q&A
    # ==========================================

    def query_documents(
        self,
        question: str,
        document_ids: Optional[list[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.05,
    ) -> dict[str, Any]:
        """
        Execute RAG question-answering across multiple documents or the whole repository.
        """
        if not question or not question.strip():
            return {
                "answer": "Please provide a valid question.",
                "sources": [],
                "citations": [],
                "method": "input_validation",
            }

        clean_q = question.strip()

        # 1. Embed query
        q_emb = self.embedding_model.embed_query(clean_q)

        # 2. Vector retrieval across specified documents or all
        filter_dict = {"document_ids": document_ids} if document_ids else None
        scored_chunks = self.vector_store.query(
            query_vector=q_emb,
            top_k=top_k,
            filter_dict=filter_dict,
            min_similarity=min_similarity,
        )

        if not scored_chunks:
            return {
                "answer": GROUNDING_FALLBACK_TEXT,
                "sources": [],
                "citations": [],
                "method": "grounding_guardrail",
            }

        # 3. Construct grounded prompt
        system_prompt, user_prompt = build_grounded_rag_prompt(
            question=clean_q,
            scored_chunks=scored_chunks,
            document_type="Repository-Wide",
        )

        # 4. Generate answer
        llm_response = self.llm_client.generate_grounded_answer(
            question=clean_q,
            scored_chunks=scored_chunks,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # 5. Format sources
        sources = self._build_source_citations(scored_chunks)
        citations = llm_response.get("citations", [])
        if not citations and sources and llm_response["answer"] != GROUNDING_FALLBACK_TEXT:
            top_src = sources[0]
            citations = [f"{top_src['filename'] or 'Document'} — Page {top_src['page_number']}"]

        return {
            "answer": llm_response["answer"],
            "sources": sources,
            "citations": citations,
            "method": llm_response.get("method", "rag"),
        }

    def _build_source_citations(
        self,
        scored_chunks: list[ScoredChunk],
    ) -> list[dict[str, Any]]:
        """Construct structured source items from retrieved chunks."""
        sources = []
        for sc in scored_chunks:
            c = sc.chunk
            snippet = c.text[:220].strip()
            if len(c.text) > 220:
                snippet += "..."

            sources.append({
                "document_id": c.document_id,
                "filename": c.filename or "Document",
                "page_number": c.page_number,
                "chunk_id": c.chunk_id,
                "chunk_type": c.chunk_type,
                "snippet": snippet,
                "similarity_score": round(float(sc.score), 4),
            })
        return sources


# Global pipeline singleton
_RAG_PIPELINE_CACHE: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """Retrieve global RAGPipeline singleton."""
    global _RAG_PIPELINE_CACHE
    if _RAG_PIPELINE_CACHE is None:
        _RAG_PIPELINE_CACHE = RAGPipeline()
    return _RAG_PIPELINE_CACHE


def reset_rag_pipeline() -> None:
    """Reset global RAGPipeline singleton (primarily for tests)."""
    global _RAG_PIPELINE_CACHE
    _RAG_PIPELINE_CACHE = None
