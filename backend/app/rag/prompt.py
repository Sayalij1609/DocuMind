"""
Grounded RAG Prompt Engineering for Nexora.

Implements strict anti-hallucination guardrails, page citation instructions,
and Rupee (₹) formatting standards.
"""

from typing import Optional
from app.rag.vector_store import ScoredChunk

GROUNDING_FALLBACK_TEXT = "I could not find this information in the uploaded documents."


def build_grounded_rag_prompt(
    question: str,
    scored_chunks: list[ScoredChunk],
    document_type: Optional[str] = None,
) -> tuple[str, str]:
    """
    Constructs the (system_prompt, user_prompt) pair for grounded Q&A.

    Enforces:
      1. Strictly answering only from provided context chunks.
      2. Returning GROUNDING_FALLBACK_TEXT if information is missing.
      3. Never inventing or hallucinating values.
      4. Formatting all monetary amounts in Indian Rupees (₹).
      5. Explicitly citing document filenames and page numbers.
    """
    system_prompt = (
        "You are Nexora, an enterprise document intelligence and question-answering assistant.\n"
        "Your task is to provide clear, beautifully structured, accurate answers based on the retrieved context.\n\n"
        "CORE INSTRUCTIONS:\n"
        "1. Structure your answers professionally using Markdown (bold highlights, clear bullet points, or markdown tables when listing items, bills, or figures).\n"
        "2. Ground your answer strictly in the provided document context. Do not invent outside facts or numbers.\n"
        "3. Be resilient to OCR noise, typos, and table scanning anomalies (e.g., 'Bit' or 'Bil' for Bill, 'Hectic Bil' for Electric Bill, 'Rent ait' for Rent Bill, broken lines, numbers without decimals).\n"
        "4. If the user asks for a list (e.g., bills, transactions, line items, deposits, withdrawals), extract and present them in a clean markdown table or structured list with dates and amounts.\n"
        "5. If a question asks for a field not directly matching the document type (e.g., asking for an 'invoice total' on a bank statement), clarify the document type politely and provide the relevant financial figures (such as ending balance or total money out).\n"
        f"6. If the document genuinely does not contain the requested topic, respond with: \"{GROUNDING_FALLBACK_TEXT}\"\n"
        "7. Format currency appropriately using the document's currency symbol ($ or ₹ for Indian invoices).\n"
        "8. Cite the source document and page number.\n\n"
        "Respond in valid JSON format:\n"
        "{\n"
        '  "answer": "Structured markdown answer here...",\n'
        '  "citations": ["Invoice.pdf — Page 2"]\n'
        "}"
    )

    context_blocks = []
    for idx, scored in enumerate(scored_chunks, 1):
        chunk = scored.chunk
        page_str = f"Page {chunk.page_number}" if chunk.page_number else "Page 1"
        source_label = f"{chunk.filename or 'Document'} — {page_str}"
        type_note = f" [{chunk.chunk_type}]" if chunk.chunk_type == "structured_entity" else ""

        block = (
            f"--- CHUNK {idx} | Source: {source_label}{type_note} "
            f"(Similarity: {scored.score:.2f}) ---\n"
            f"{chunk.text}\n"
        )
        context_blocks.append(block)

    joined_context = "\n".join(context_blocks) if context_blocks else "[No relevant context found]"

    user_prompt = (
        f"DOCUMENT TYPE: {document_type or 'General'}\n\n"
        f"=== RETRIEVED CONTEXT ===\n"
        f"{joined_context}\n"
        f"=== END CONTEXT ===\n\n"
        f"User Question: {question}"
    )

    return system_prompt, user_prompt
