"""
Comprehensive Automated Test Suite for Phase 12: RAG-Based Document Q&A.

Tests all required criteria:
  1. Answerable question
  2. Unanswerable question (grounding guardrail)
  3. Wrong document isolation (metadata filtering)
  4. Multiple documents (cross-document repository search)
  5. Empty document handling
  6. Retrieval failure / low similarity threshold
  7. LLM failure graceful fallback
  8. Source attribution (document_id, filename, page_number, snippet)
"""

from unittest.mock import MagicMock, patch
import pytest

from app.rag.chunking import DocumentChunk, PageAwareChunker
from app.rag.embeddings import DenseHashingEmbeddingModel, get_embedding_model
from app.rag.llm import RAGLLMClient
from app.rag.pipeline import RAGPipeline
from app.rag.prompt import GROUNDING_FALLBACK_TEXT, build_grounded_rag_prompt
from app.rag.vector_store import PersistentVectorStore


class MockDocumentPage:
    """Mock representing a database DocumentPage object."""

    def __init__(self, page_number: int, cleaned_text: str):
        self.page_number = page_number
        self.cleaned_text = cleaned_text
        self.raw_text = cleaned_text


@pytest.fixture
def test_pipeline(tmp_path):
    """Provides an isolated RAGPipeline backed by a temporary vector store."""
    store_file = tmp_path / "test_vector_index.json"
    chunker = PageAwareChunker(chunk_size=300, chunk_overlap=50)
    embedding_model = DenseHashingEmbeddingModel(dimension=256)
    vector_store = PersistentVectorStore(storage_path=str(store_file))
    llm_client = RAGLLMClient(api_key=None)  # Uses deterministic fallback

    pipeline = RAGPipeline(
        chunker=chunker,
        embedding_model=embedding_model,
        vector_store=vector_store,
        llm_client=llm_client,
    )
    return pipeline


# ========================================================
# 1. Answerable Question Test
# ========================================================
def test_answerable_question(test_pipeline):
    """Verify that an answerable question correctly returns factual content and citations."""
    pages = [
        MockDocumentPage(
            page_number=1,
            cleaned_text=(
                "TAX INVOICE\n"
                "Vendor: Global Systems India Pvt Ltd\n"
                "Invoice Number: INV-98234\n"
                "Date: 2024-04-10"
            ),
        ),
        MockDocumentPage(
            page_number=2,
            cleaned_text=(
                "Description of Services: Cloud Infrastructure Consulting.\n"
                "Subtotal: ₹85,500.00\n"
                "GST @ 18%: ₹15,390.00\n"
                "Total Amount Due: ₹100,890.00"
            ),
        ),
    ]

    extraction_data = {
        "invoice_total": "100890.00",
        "vendor_name": "Global Systems India Pvt Ltd",
        "invoice_number": "INV-98234",
    }

    test_pipeline.index_document(
        document_id="doc_inv_101",
        document_type="invoice",
        filename="Cloud_Invoice.pdf",
        pages=pages,
        extraction_data=extraction_data,
    )

    # Ask about the invoice total
    res = test_pipeline.query_document(
        document_id="doc_inv_101",
        question="What is the invoice total?",
        document_type="invoice",
    )

    assert "100,890" in res["answer"] or "100890" in res["answer"]
    assert "₹" in res["answer"]
    assert len(res["sources"]) > 0
    # Provenance check
    assert res["sources"][0]["document_id"] == "doc_inv_101"
    assert res["sources"][0]["filename"] == "Cloud_Invoice.pdf"
    assert res["answer"] != GROUNDING_FALLBACK_TEXT


# ========================================================
# 2. Unanswerable Question Test (Strict Grounding)
# ========================================================
def test_unanswerable_question(test_pipeline):
    """Verify that asking about missing information triggers the grounding fallback."""
    pages = [
        MockDocumentPage(
            page_number=1,
            cleaned_text="Standard Purchase Order for Office Supplies.",
        )
    ]

    test_pipeline.index_document(
        document_id="doc_po_202",
        document_type="purchase_order",
        filename="PO_202.pdf",
        pages=pages,
    )

    # Question asking for completely absent data
    res = test_pipeline.query_document(
        document_id="doc_po_202",
        question="What is the employee's favorite pizza topping and shoe size?",
    )

    assert res["answer"] == GROUNDING_FALLBACK_TEXT
    assert "shoe size" not in res["answer"].lower()


# ========================================================
# 3. Wrong Document Test (Metadata Isolation)
# ========================================================
def test_wrong_document(test_pipeline):
    """
    Verify metadata filtering isolates documents:
    Querying Document A for content in Document B should return nothing from B.
    """
    # Doc A: Laptop purchase
    test_pipeline.index_document(
        document_id="doc_A",
        document_type="receipt",
        filename="MacBook_Receipt.pdf",
        fallback_text="Purchased 1x Apple MacBook Pro for ₹250,000.",
    )

    # Doc B: Printer maintenance
    test_pipeline.index_document(
        document_id="doc_B",
        document_type="receipt",
        filename="Printer_Receipt.pdf",
        fallback_text="Purchased 4x Laser Toner Cartridges for ₹12,000.",
    )

    # Query Doc A asking about Toner cartridges
    res_a = test_pipeline.query_document(
        document_id="doc_A",
        question="How much were the Laser Toner Cartridges?",
    )

    # Must NOT return Document B's answer or sources
    for src in res_a["sources"]:
        assert src["document_id"] != "doc_B"
        assert "Toner" not in src["snippet"]

    assert res_a["answer"] == GROUNDING_FALLBACK_TEXT


# ========================================================
# 4. Multiple Documents Test (Repository Search)
# ========================================================
def test_multiple_documents(test_pipeline):
    """Verify repository-wide search retrieves relevant chunks across multiple documents."""
    test_pipeline.index_document(
        document_id="doc_contract",
        document_type="contract",
        filename="Vendor_Agreement.pdf",
        fallback_text="Section 4: The agreement term shall be 36 months expiring on 2027-12-31.",
    )
    test_pipeline.index_document(
        document_id="doc_invoice",
        document_type="invoice",
        filename="March_Invoice.pdf",
        fallback_text="Total Amount Due: ₹45,000 for monthly recurring SaaS billing.",
    )

    # Query across all documents
    res = test_pipeline.query_documents(
        question="What is the agreement term length?",
    )

    assert len(res["sources"]) > 0
    # Top source should be from the contract
    assert res["sources"][0]["document_id"] == "doc_contract"
    assert "36 months" in res["sources"][0]["snippet"]


# ========================================================
# 5. Empty Document Test
# ========================================================
def test_empty_document(test_pipeline):
    """Verify that an empty document is indexed safely and handled gracefully."""
    count = test_pipeline.index_document(
        document_id="doc_empty",
        document_type="unknown",
        filename="Blank.pdf",
        pages=[],
        fallback_text="",
    )

    assert count == 0

    res = test_pipeline.query_document(
        document_id="doc_empty",
        question="What is the invoice total?",
    )

    assert res["answer"] == GROUNDING_FALLBACK_TEXT
    assert res["sources"] == []


# ========================================================
# 6. Retrieval Failure Test (Low Similarity Threshold)
# ========================================================
def test_retrieval_failure(test_pipeline):
    """Verify pipeline behavior when no chunks pass the similarity threshold."""
    test_pipeline.index_document(
        document_id="doc_medical",
        document_type="medical_report",
        filename="Health.pdf",
        fallback_text="Patient showed normal blood pressure and vitals.",
    )

    # Extremely high similarity threshold that fails all chunks
    res = test_pipeline.query_document(
        document_id="doc_medical",
        question="What are the quarterly semiconductor export earnings?",
        min_similarity=0.99,
    )

    assert res["answer"] == GROUNDING_FALLBACK_TEXT
    assert res["sources"] == []


# ========================================================
# 7. LLM Failure Test (Graceful Fallback)
# ========================================================
def test_llm_failure_fallback(tmp_path):
    """Verify that when the LLM provider fails, deterministic extraction gracefully answers."""
    store_file = tmp_path / "test_llm_fail.json"
    chunker = PageAwareChunker()
    embedding_model = DenseHashingEmbeddingModel(dimension=256)
    vector_store = PersistentVectorStore(storage_path=str(store_file))

    # Mock LLM client that raises an exception
    failing_llm = RAGLLMClient(api_key="mock_key")
    failing_llm._call_groq = MagicMock(side_effect=RuntimeError("Groq API Timeout"))

    pipeline = RAGPipeline(
        chunker=chunker,
        embedding_model=embedding_model,
        vector_store=vector_store,
        llm_client=failing_llm,
    )

    pages = [
        MockDocumentPage(
            page_number=1,
            cleaned_text="Invoice Total: ₹54,200.00\nBilled By: Acme Corp",
        )
    ]

    pipeline.index_document(
        document_id="doc_fallback_test",
        document_type="invoice",
        filename="Acme.pdf",
        pages=pages,
    )

    # Even though LLM raises an error, pipeline must not crash and should fall back gracefully
    res = pipeline.query_document(
        document_id="doc_fallback_test",
        question="What is the invoice total?",
    )

    assert "54,200" in res["answer"]
    assert "₹" in res["answer"]
    assert res["method"] == "deterministic_extraction"


# ========================================================
# 8. Source Attribution Test
# ========================================================
def test_source_attribution(test_pipeline):
    """Verify that retrieved sources provide complete provenance metadata."""
    pages = [
        MockDocumentPage(
            page_number=3,
            cleaned_text="Line item: Premium Support Subscription 12 Months. Total: ₹60,000.",
        )
    ]

    test_pipeline.index_document(
        document_id="doc_prov_1",
        document_type="invoice",
        filename="Support_Contract.pdf",
        pages=pages,
    )

    res = test_pipeline.query_document(
        document_id="doc_prov_1",
        question="How much is the Premium Support Subscription?",
    )

    assert len(res["sources"]) > 0
    src = res["sources"][0]
    assert src["document_id"] == "doc_prov_1"
    assert src["filename"] == "Support_Contract.pdf"
    assert src["page_number"] == 3
    assert src["chunk_id"].startswith("doc_prov_1_p3")
    assert "Premium Support" in src["snippet"]
    assert src["similarity_score"] > 0
