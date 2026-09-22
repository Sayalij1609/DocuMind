"""
PDF Report Generation Service.

Generates professional PDF reports for processed documents
using fpdf2. Each report includes:
  - Document metadata
  - Classification result
  - Extracted fields
  - Validation results
  - Anomaly detection
  - Duplicate check
  - Confidence scores
"""

import io
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.services.document_repository import (
    DocumentRepository,
)
from app.services.extraction_result_repository import (
    ExtractionResultRepository,
)
from app.services.validation_result_repository import (
    ValidationResultRepository,
)
from app.services.document_content_repository import (
    DocumentContentRepository,
)
from app.services.anomaly_result_repository import (
    AnomalyResultRepository,
)
from app.services.duplicate_result_repository import (
    DuplicateResultRepository,
)

logger = logging.getLogger(__name__)

# Brand colors
COLOR_PRIMARY = (37, 99, 235)
COLOR_DARK = (15, 23, 42)
COLOR_GRAY = (100, 116, 139)
COLOR_LIGHT_BG = (248, 250, 252)
COLOR_SUCCESS = (22, 163, 74)
COLOR_ERROR = (220, 38, 38)
COLOR_WARNING = (234, 179, 8)
COLOR_WHITE = (255, 255, 255)


class ReportService:
    """Generate PDF reports for document analysis results."""

    @staticmethod
    def _safe_text(text) -> str:
        """Sanitize text for latin-1 compatible PDF fonts."""
        if text is None:
            return ""
        s = str(text)
        # Replace common Unicode with ASCII equivalents
        replacements = {
            "\u2014": "-",   # em dash
            "\u2013": "-",   # en dash
            "\u2018": "'",   # left single quote
            "\u2019": "'",   # right single quote
            "\u201c": '"',   # left double quote
            "\u201d": '"',   # right double quote
            "\u2022": "*",   # bullet
            "\u2026": "...", # ellipsis
            "\u00a0": " ",   # non-breaking space
            "\u20b9": "Rs.", # rupee sign
            "\u20ac": "EUR", # euro sign
            "\u00a3": "GBP", # pound sign
            "\u2265": ">=",  # greater than or equal
            "\u2264": "<=",  # less than or equal
        }
        for old, new in replacements.items():
            s = s.replace(old, new)
        # Strip any remaining non-latin-1 characters
        s = s.encode("latin-1", errors="replace").decode("latin-1")
        return s

    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.ext_repo = ExtractionResultRepository(db)
        self.val_repo = ValidationResultRepository(db)
        self.content_repo = DocumentContentRepository(db)
        self.anomaly_repo = AnomalyResultRepository(db)
        self.dup_repo = DuplicateResultRepository(db)

    def generate_pdf(
        self,
        document_id: str,
    ) -> bytes:
        """
        Generate a full PDF report for a document.

        Returns:
            PDF file as bytes.

        Raises:
            ValueError: If document not found.
        """
        from fpdf import FPDF

        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            raise ValueError("Document not found")

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # ── Title / Header ──
        self._draw_header(pdf, doc)

        # ── Document Metadata ──
        self._draw_section_title(pdf, "Document Information")
        self._draw_metadata_table(pdf, doc)

        # ── Classification ──
        self._draw_section_title(pdf, "Classification")
        self._draw_classification(pdf, doc)

        # ── Extracted Fields ──
        ext_rec = self.ext_repo.get_by_document_id(
            document_id
        )
        if ext_rec and ext_rec.extracted_fields:
            self._draw_section_title(
                pdf, "Extracted Fields"
            )
            self._draw_extraction(pdf, ext_rec)

        # ── Validation ──
        val_rec = self.val_repo.get_by_document_id(
            document_id
        )
        if val_rec and val_rec.rule_results:
            self._draw_section_title(
                pdf, "Validation Results"
            )
            self._draw_validation(pdf, val_rec)

        # ── Anomaly Detection ──
        anomaly_rec = (
            self.anomaly_repo.get_by_document_id(
                document_id
            )
        )
        if anomaly_rec:
            self._draw_section_title(
                pdf, "Anomaly Detection"
            )
            self._draw_anomaly(pdf, anomaly_rec)

        # ── Duplicate Check ──
        dup_matches = (
            self.dup_repo.get_by_document_id(
                document_id
            )
        )
        if dup_matches:
            self._draw_section_title(
                pdf, "Duplicate Check"
            )
            self._draw_duplicates(pdf, dup_matches)

        # ── AI Analysis Summary ──
        ai_analysis = self.doc_repo.get_ai_analysis(
            document_id
        )
        if ai_analysis:
            self._draw_section_title(
                pdf, "AI Analysis Summary"
            )
            self._draw_ai_summary(pdf, ai_analysis)

        # ── Footer ──
        self._draw_footer(pdf)

        return bytes(pdf.output())

    # ── Drawing Helpers ──

    def _draw_header(self, pdf, doc):
        """Draw report title and branding."""
        # Blue header bar
        pdf.set_fill_color(*COLOR_PRIMARY)
        pdf.rect(10, 10, 190, 28, "F")

        pdf.set_text_color(*COLOR_WHITE)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(16, 14)
        pdf.cell(0, 10, "NEXORA", new_x="LMARGIN")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_xy(16, 24)
        pdf.cell(
            0, 8,
            "Document Analysis Report",
            new_x="LMARGIN",
        )

        # Right side: date
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(140, 14)
        now = datetime.now(timezone.utc)
        pdf.cell(
            54, 10,
            f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
            align="R",
        )

        pdf.set_text_color(*COLOR_DARK)
        pdf.set_y(44)

    def _draw_section_title(self, pdf, title: str):
        """Draw a section heading."""
        if pdf.get_y() > 260:
            pdf.add_page()

        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

        # Underline
        pdf.set_draw_color(*COLOR_PRIMARY)
        pdf.set_line_width(0.5)
        y = pdf.get_y()
        pdf.line(10, y, 200, y)
        pdf.ln(4)
        pdf.set_text_color(*COLOR_DARK)

    def _draw_kv_row(
        self, pdf, key: str, value: str,
        alt: bool = False
    ):
        """Draw a key-value row."""
        if alt:
            pdf.set_fill_color(*COLOR_LIGHT_BG)
        else:
            pdf.set_fill_color(*COLOR_WHITE)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.cell(
            55, 7, key, fill=True,
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*COLOR_DARK)

        # Truncate long values
        display_val = self._safe_text(str(value)[:100]) if value else "-"
        pdf.cell(
            135, 7, display_val, fill=True,
            new_x="LMARGIN", new_y="NEXT",
        )

    def _draw_metadata_table(self, pdf, doc):
        """Draw document metadata."""
        rows = [
            ("Document ID", doc.document_id),
            ("Filename", doc.filename),
            ("File Type", doc.file_type),
            (
                "File Size",
                self._format_bytes(doc.file_size),
            ),
            ("Status", doc.status.value if hasattr(doc.status, 'value') else str(doc.status)),
            (
                "Created",
                (
                    doc.created_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if doc.created_at
                    else "—"
                ),
            ),
        ]
        for i, (k, v) in enumerate(rows):
            self._draw_kv_row(pdf, k, v, alt=i % 2 == 0)

    def _draw_classification(self, pdf, doc):
        """Draw classification results."""
        rows = [
            (
                "Document Type",
                doc.document_type or "Not classified",
            ),
            (
                "Confidence",
                (
                    f"{doc.classification_confidence:.4f}"
                    if doc.classification_confidence
                    else "—"
                ),
            ),
            (
                "Classified At",
                (
                    doc.classified_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if doc.classified_at
                    else "—"
                ),
            ),
        ]
        for i, (k, v) in enumerate(rows):
            self._draw_kv_row(pdf, k, v, alt=i % 2 == 0)

    def _draw_extraction(self, pdf, ext_rec):
        """Draw extracted fields table."""
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*COLOR_PRIMARY)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.cell(55, 7, "Field", fill=True)
        pdf.cell(80, 7, "Value", fill=True)
        pdf.cell(
            55, 7, "Confidence", fill=True,
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.set_text_color(*COLOR_DARK)

        fields = ext_rec.extracted_fields or {}
        for i, (name, fd) in enumerate(fields.items()):
            if pdf.get_y() > 270:
                pdf.add_page()

            alt = i % 2 == 0
            if alt:
                pdf.set_fill_color(*COLOR_LIGHT_BG)
            else:
                pdf.set_fill_color(*COLOR_WHITE)

            val = "-"
            conf = "-"
            if isinstance(fd, dict):
                val = self._safe_text(str(fd.get("value", "-"))[:60])
                c = fd.get("confidence")
                if c is not None:
                    conf = f"{float(c):.4f}"

            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(55, 7, self._safe_text(name), fill=True)
            pdf.set_font("Helvetica", "", 8)
            pdf.cell(80, 7, val, fill=True)
            pdf.cell(
                55, 7, conf, fill=True,
                new_x="LMARGIN", new_y="NEXT",
            )

    def _draw_validation(self, pdf, val_rec):
        """Draw validation results."""
        rules = val_rec.rule_results or []
        passed = sum(
            1 for r in rules
            if r.get("status") == "PASS"
        )
        failed = sum(
            1 for r in rules
            if r.get("status") == "FAIL"
        )

        self._draw_kv_row(
            pdf, "Status",
            val_rec.status or "Unknown",
            alt=True,
        )
        self._draw_kv_row(
            pdf, "Rules Passed",
            str(passed),
        )
        self._draw_kv_row(
            pdf, "Rules Failed",
            str(failed),
            alt=True,
        )

        pdf.ln(3)

        # Rule detail table
        if rules:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(*COLOR_PRIMARY)
            pdf.set_text_color(*COLOR_WHITE)
            pdf.cell(70, 7, "Rule", fill=True)
            pdf.cell(25, 7, "Status", fill=True)
            pdf.cell(
                95, 7, "Message", fill=True,
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_text_color(*COLOR_DARK)

            for i, r in enumerate(rules[:20]):
                if pdf.get_y() > 270:
                    pdf.add_page()

                alt = i % 2 == 0
                if alt:
                    pdf.set_fill_color(*COLOR_LIGHT_BG)
                else:
                    pdf.set_fill_color(*COLOR_WHITE)

                status = r.get("status", "-")
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(
                    70, 7,
                    self._safe_text(str(r.get("rule_name", "-"))[:40]),
                    fill=True,
                )

                if status == "PASS":
                    pdf.set_text_color(*COLOR_SUCCESS)
                elif status == "FAIL":
                    pdf.set_text_color(*COLOR_ERROR)
                else:
                    pdf.set_text_color(*COLOR_WARNING)

                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(25, 7, status, fill=True)
                pdf.set_text_color(*COLOR_DARK)
                pdf.set_font("Helvetica", "", 8)
                pdf.cell(
                    95, 7,
                    self._safe_text(str(r.get("message", ""))[:55]),
                    fill=True,
                    new_x="LMARGIN", new_y="NEXT",
                )

    def _draw_anomaly(self, pdf, anomaly_rec):
        """Draw anomaly detection results."""
        is_anom = anomaly_rec.is_anomaly
        self._draw_kv_row(
            pdf, "Is Anomaly",
            "Yes - Flagged" if is_anom else "No - Normal",
            alt=True,
        )
        self._draw_kv_row(
            pdf, "Anomaly Score",
            f"{anomaly_rec.anomaly_score:.4f}",
        )
        self._draw_kv_row(
            pdf, "Decision Score",
            f"{anomaly_rec.decision_function_score:.4f}",
            alt=True,
        )

    def _draw_duplicates(self, pdf, dup_matches):
        """Draw duplicate detection results."""
        self._draw_kv_row(
            pdf, "Matches Found",
            str(len(dup_matches)),
            alt=True,
        )

        for i, m in enumerate(dup_matches[:10]):
            matched_id = (
                m.matched_document_id
                if hasattr(m, "matched_document_id")
                else str(m)
            )
            score = (
                f"{m.similarity_score:.4f}"
                if hasattr(m, "similarity_score")
                else "-"
            )
            dup_type = (
                m.duplicate_type
                if hasattr(m, "duplicate_type")
                else "-"
            )
            self._draw_kv_row(
                pdf,
                f"Match {i + 1}",
                self._safe_text(f"{matched_id[:24]}.. | {score} | {dup_type}"),
                alt=i % 2 == 0,
            )

    def _draw_ai_summary(self, pdf, ai_analysis: dict):
        """Draw AI analysis summary."""
        summary = ai_analysis.get(
            "executive_summary", ""
        )
        if summary:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*COLOR_DARK)
            pdf.multi_cell(
                0, 5,
                self._safe_text(str(summary)[:800]),
            )
            pdf.ln(3)

        method = ai_analysis.get(
            "analysis_method", "unknown"
        )
        self._draw_kv_row(
            pdf, "Analysis Method",
            method,
            alt=True,
        )

    def _draw_footer(self, pdf):
        """Draw report footer."""
        pdf.ln(10)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*COLOR_GRAY)
        pdf.cell(
            0, 6,
            (
                "This report was auto-generated by "
                "Nexora Document Intelligence Platform. "
                "Confidential."
            ),
            new_x="LMARGIN", new_y="NEXT",
            align="C",
        )

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human-readable string."""
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"
