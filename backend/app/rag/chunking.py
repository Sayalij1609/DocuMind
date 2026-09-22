"""
Page-Aware Document Chunking for Nexora RAG.

Splits document text on a page-by-page basis into semantically coherent,
overlapping chunks while retaining full provenance metadata (document_id,
page_number, chunk_id, document_type, filename).

Also creates structured entity chunks from deterministic extraction results
so that exact financial values (e.g. Invoice Total in ₹) are preserved.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Optional


@dataclass
class DocumentChunk:
    """Represents an indexed chunk of text with complete provenance metadata."""

    chunk_id: str
    document_id: str
    page_number: int
    text: str
    document_type: str = "unknown"
    filename: str = ""
    chunk_type: str = "page_text"  # "page_text" | "structured_entity"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "text": self.text,
            "document_type": self.document_type,
            "filename": self.filename,
            "chunk_type": self.chunk_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentChunk":
        return cls(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            page_number=data.get("page_number", 1),
            text=data["text"],
            document_type=data.get("document_type", "unknown"),
            filename=data.get("filename", ""),
            chunk_type=data.get("chunk_type", "page_text"),
            metadata=data.get("metadata", {}),
        )


class PageAwareChunker:
    """Creates page-aware chunks from document pages and extraction results."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        min_chunk_size: int = 20,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def split_text_into_chunks(self, text: str) -> list[str]:
        """Split a string into overlapping chunks respecting sentence/line boundaries."""
        clean_text = text.strip()
        if not clean_text or len(clean_text) < self.min_chunk_size:
            return []

        if len(clean_text) <= self.chunk_size:
            return [clean_text]

        chunks = []
        # Split primarily on double newlines (paragraphs) or single newlines
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", clean_text) if p.strip()]

        current_chunk = ""
        for para in paragraphs:
            if not current_chunk:
                current_chunk = para
            elif len(current_chunk) + len(para) + 1 <= self.chunk_size:
                current_chunk += "\n" + para
            else:
                chunks.append(current_chunk)
                # Apply overlap: take the trailing characters from current_chunk
                overlap_text = current_chunk[-self.chunk_overlap :] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = (overlap_text + "\n" + para).strip()

        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)

        # Fallback if text has no newlines and was longer than chunk_size
        if not chunks and len(clean_text) > self.chunk_size:
            start = 0
            while start < len(clean_text):
                end = min(start + self.chunk_size, len(clean_text))
                chunk_slice = clean_text[start:end].strip()
                if len(chunk_slice) >= self.min_chunk_size:
                    chunks.append(chunk_slice)
                start += self.chunk_size - self.chunk_overlap

        return chunks

    def chunk_page(
        self,
        text: str,
        document_id: str,
        page_number: int,
        document_type: str = "unknown",
        filename: str = "",
    ) -> list[DocumentChunk]:
        """Create page-aware chunks for a single document page."""
        raw_chunks = self.split_text_into_chunks(text)
        result: list[DocumentChunk] = []

        for idx, chunk_text in enumerate(raw_chunks):
            chunk_id = f"{document_id}_p{page_number}_c{idx}"
            result.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    page_number=page_number,
                    text=chunk_text,
                    document_type=document_type,
                    filename=filename,
                    chunk_type="page_text",
                    metadata={
                        "page_number": page_number,
                        "chunk_index": idx,
                        "char_count": len(chunk_text),
                    },
                )
            )

        return result

    def build_structured_entity_chunk(
        self,
        document_id: str,
        document_type: str,
        filename: str,
        extraction_data: dict[str, Any],
        page_number: int = 1,
    ) -> Optional[DocumentChunk]:
        """
        Creates a high-fidelity synthetic chunk containing verified deterministic
        extracted fields (Total, Invoice #, Vendor, Dates, Line items) with Rupee (₹)
        formatting. Ensures exact values are readily retrievable.
        """
        if not extraction_data:
            return None

        lines = ["--- VERIFIED STRUCTURED EXTRACTION ---"]
        has_content = False

        # Extract fields from dictionary or FieldResult objects
        fields = extraction_data.get("fields", extraction_data)
        if isinstance(fields, dict):
            for key, val in fields.items():
                if val is None or val == "":
                    continue
                # Handle FieldResult object or dict
                if isinstance(val, dict):
                    field_val = val.get("value")
                    conf = val.get("confidence", 1.0)
                elif hasattr(val, "value"):
                    field_val = getattr(val, "value")
                    conf = getattr(val, "confidence", 1.0)
                else:
                    field_val = val
                    conf = 1.0

                if field_val is not None and str(field_val).strip():
                    readable_key = key.replace("_", " ").title()
                    # Format financial amounts with Rupee symbol
                    if any(curr in key.lower() for curr in ["total", "amount", "tax", "subtotal", "price"]):
                        val_str = str(field_val).strip()
                        if not val_str.startswith("₹") and not val_str.startswith("Rs"):
                            field_val = f"₹{field_val}"
                    lines.append(f"{readable_key}: {field_val} (Confidence: {conf:.2f})")
                    has_content = True

        if not has_content:
            return None

        text = "\n".join(lines)
        return DocumentChunk(
            chunk_id=f"{document_id}_structured_entity",
            document_id=document_id,
            page_number=page_number,
            text=text,
            document_type=document_type,
            filename=filename,
            chunk_type="structured_entity",
            metadata={
                "page_number": page_number,
                "is_structured_extraction": True,
            },
        )

    def create_chunks(
        self,
        document_id: str,
        document_type: str = "unknown",
        filename: str = "",
        pages: Optional[list[Any]] = None,
        fallback_text: str = "",
        extraction_data: Optional[dict[str, Any]] = None,
    ) -> list[DocumentChunk]:
        """
        Comprehensive chunk generator. Processes all pages, creates structured
        entity chunk if available, or falls back to full document text if pages
        are empty.
        """
        all_chunks: list[DocumentChunk] = []

        # 1. Structured entity chunk (high priority for deterministic exact values)
        if extraction_data:
            struct_chunk = self.build_structured_entity_chunk(
                document_id=document_id,
                document_type=document_type,
                filename=filename,
                extraction_data=extraction_data,
            )
            if struct_chunk:
                all_chunks.append(struct_chunk)

        # 2. Page-aware chunks
        if pages:
            for page in pages:
                page_num = getattr(page, "page_number", 1)
                page_text = (
                    getattr(page, "cleaned_text", None)
                    or getattr(page, "raw_text", None)
                    or ""
                )
                if page_text.strip():
                    p_chunks = self.chunk_page(
                        text=page_text,
                        document_id=document_id,
                        page_number=page_num,
                        document_type=document_type,
                        filename=filename,
                    )
                    all_chunks.extend(p_chunks)

        # 3. Fallback to general text if no page chunks could be generated
        if not any(c.chunk_type == "page_text" for c in all_chunks) and fallback_text.strip():
            raw_chunks = self.split_text_into_chunks(fallback_text)
            for idx, text in enumerate(raw_chunks):
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}_fallback_c{idx}",
                        document_id=document_id,
                        page_number=1,
                        text=text,
                        document_type=document_type,
                        filename=filename,
                        chunk_type="page_text",
                        metadata={"page_number": 1, "is_fallback": True},
                    )
                )

        return all_chunks
