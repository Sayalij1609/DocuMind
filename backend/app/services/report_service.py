"""
Documind - Professional PDF Report Generator.

Clean, single-flow PDF with branded header on page 1,
content starting immediately. No cover page, no TOC.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.services.document_repository import DocumentRepository
from app.services.extraction_result_repository import ExtractionResultRepository
from app.services.validation_result_repository import ValidationResultRepository
from app.services.document_content_repository import DocumentContentRepository
from app.services.anomaly_result_repository import AnomalyResultRepository
from app.services.duplicate_result_repository import DuplicateResultRepository

logger = logging.getLogger(__name__)

# Colors
C_PRIMARY = (37, 99, 235)
C_DARK = (15, 23, 42)
C_GRAY = (100, 116, 139)
C_LGRAY = (203, 213, 225)
C_BG = (248, 250, 252)
C_BLUE_BG = (239, 246, 255)
C_GREEN = (22, 163, 74)
C_RED = (220, 38, 38)
C_YELLOW = (180, 140, 8)
C_WHITE = (255, 255, 255)
C_GREEN_BG = (240, 253, 244)
C_RED_BG = (254, 242, 242)
C_YELLOW_BG = (254, 252, 232)


def _safe(text) -> str:
    if text is None:
        return ""
    s = str(text)
    for old, new in {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u2026": "...",
        "\u00a0": " ", "\u20b9": "Rs.", "\u20ac": "EUR", "\u00a3": "GBP",
        "\u2265": ">=", "\u2264": "<=", "\u2192": "->", "\u2713": "[Y]",
        "\u2717": "[X]", "\u00b7": ".", "\u00d7": "x",
    }.items():
        s = s.replace(old, new)
    return s.encode("latin-1", errors="replace").decode("latin-1")


def _fmt_bytes(size) -> str:
    if not size:
        return "0 B"
    if size < 1024:
        return f"{size} B"
    if size < 1048576:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1048576:.1f} MB"


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.ext_repo = ExtractionResultRepository(db)
        self.val_repo = ValidationResultRepository(db)
        self.content_repo = DocumentContentRepository(db)
        self.anomaly_repo = AnomalyResultRepository(db)
        self.dup_repo = DuplicateResultRepository(db)

    def generate_pdf(self, document_id: str) -> bytes:
        from fpdf import FPDF

        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            raise ValueError("Document not found")

        # Gather data
        content_rec = self.content_repo.get_by_document_id(document_id)
        ext_rec = self.ext_repo.get_by_document_id(document_id)
        val_rec = self.val_repo.get_by_document_id(document_id)
        anomaly_rec = self.anomaly_repo.get_by_document_id(document_id)
        dup_matches = self.dup_repo.get_by_document_id(document_id)
        ai_analysis = self.doc_repo.get_ai_analysis(document_id)

        real_fields = {}
        if ext_rec and ext_rec.extracted_fields:
            real_fields = {
                k: v for k, v in ext_rec.extracted_fields.items()
                if not k.startswith("__")
            }

        # PDF with auto footer
        class PDF(FPDF):
            def footer(fpdf):
                fpdf.set_y(-12)
                fpdf.set_font("Helvetica", "I", 7)
                fpdf.set_text_color(*C_GRAY)
                fpdf.cell(95, 5, "Documind - Confidential", align="L")
                fpdf.cell(95, 5, f"Page {fpdf.page_no()}/{{nb}}", align="R")

        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.add_page()

        # ── BRANDED HEADER (compact, on page 1) ──
        pdf.set_fill_color(*C_PRIMARY)
        pdf.rect(0, 0, 210, 36, "F")
        pdf.set_text_color(*C_WHITE)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_xy(12, 6)
        pdf.cell(0, 10, "DOCUMIND")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(12, 17)
        pdf.cell(0, 6, "Document Intelligence Report")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(12, 25)
        now = datetime.now(timezone.utc)
        pdf.cell(0, 6, _safe(f"{doc.filename}  |  {now.strftime('%B %d, %Y %H:%M UTC')}"))
        pdf.set_text_color(*C_DARK)
        pdf.set_y(42)

        # ── 1. DOCUMENT INFO ──
        self._heading(pdf, "Document Information")
        self._kv_table(pdf, [
            ("Document ID", doc.document_id),
            ("Filename", doc.filename),
            ("File Type", doc.file_type),
            ("File Size", _fmt_bytes(doc.file_size)),
            ("Status", doc.status.value if hasattr(doc.status, 'value') else str(doc.status)),
            ("Uploaded", doc.created_at.strftime("%Y-%m-%d %H:%M:%S") if doc.created_at else "-"),
        ])

        # ── 2. CLASSIFICATION ──
        self._heading(pdf, "Document Classification")
        conf = f"{doc.classification_confidence * 100:.1f}%" if doc.classification_confidence else "-"
        self._kv_table(pdf, [
            ("Document Type", doc.document_type or "Unclassified"),
            ("Confidence", conf),
            ("Classified At", doc.classified_at.strftime("%Y-%m-%d %H:%M:%S") if doc.classified_at else "-"),
        ])

        # ── 3. OCR TEXT ──
        if content_rec and content_rec.cleaned_text:
            self._heading(pdf, "Extracted Text Content")
            self._text_block(pdf, content_rec.cleaned_text)

        # ── 4. EXTRACTED FIELDS ──
        self._heading(pdf, "Extracted Data Fields")
        if real_fields:
            self._fields_table(pdf, real_fields)
        else:
            self._info_note(pdf, "No structured fields were extracted from this document.")

        # ── 5. VALIDATION ──
        self._heading(pdf, "Validation Audit")
        if val_rec and val_rec.rule_results:
            self._validation(pdf, val_rec)
        else:
            self._info_note(pdf, "No validation rules were executed.")

        # ── 6. ANOMALY ──
        self._heading(pdf, "Anomaly Detection")
        if anomaly_rec:
            self._anomaly(pdf, anomaly_rec)
        else:
            self._info_note(pdf, "Anomaly detection requires at least 5 documents in the repository.")

        # ── 7. DUPLICATES ──
        self._heading(pdf, "Duplicate Detection")
        if dup_matches and len(dup_matches) > 0:
            self._duplicates(pdf, dup_matches)
        else:
            self._info_note(pdf, "No duplicates found. This document is unique.")

        # ── 8. AI ANALYSIS ──
        self._heading(pdf, "AI Semantic Analysis")
        if ai_analysis:
            self._ai(pdf, ai_analysis)
        else:
            self._info_note(pdf, "AI analysis not performed. Configure Groq API key to enable.")

        # ── 9. SUMMARY ──
        self._heading(pdf, "Executive Summary")
        self._summary(pdf, doc, content_rec, real_fields, val_rec, anomaly_rec, dup_matches, ai_analysis)

        return bytes(pdf.output())

    # ═══════════════════════════════════════
    # BUILDING BLOCKS
    # ═══════════════════════════════════════

    def _heading(self, pdf, title):
        if pdf.get_y() > 255:
            pdf.add_page()
        pdf.ln(5)
        y = pdf.get_y()
        pdf.set_fill_color(*C_PRIMARY)
        pdf.rect(10, y, 190, 8, "F")
        pdf.set_text_color(*C_WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_xy(14, y + 1)
        pdf.cell(0, 6, _safe(title))
        pdf.set_text_color(*C_DARK)
        pdf.set_y(y + 11)

    def _kv_table(self, pdf, rows):
        pdf.set_draw_color(*C_LGRAY)
        for i, (k, v) in enumerate(rows):
            if pdf.get_y() > 272:
                pdf.add_page()
            pdf.set_fill_color(*(C_BLUE_BG if i % 2 == 0 else C_WHITE))
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(*C_GRAY)
            pdf.cell(50, 7, _safe(f"  {k}"), border=1, fill=True)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*C_DARK)
            pdf.cell(140, 7, _safe(f"  {str(v)[:110]}"), border=1, fill=True,
                     new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def _info_note(self, pdf, msg):
        pdf.set_fill_color(*C_BLUE_BG)
        pdf.set_draw_color(*C_PRIMARY)
        y = pdf.get_y()
        pdf.rect(10, y, 190, 9, "DF")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*C_GRAY)
        pdf.set_xy(14, y + 1.5)
        pdf.cell(0, 6, _safe(msg))
        pdf.set_y(y + 12)
        pdf.set_text_color(*C_DARK)

    def _text_block(self, pdf, text):
        show = text[:3500]
        if len(text) > 3500:
            show += "\n\n[... truncated ...]"
        pdf.set_fill_color(*C_BG)
        pdf.set_draw_color(*C_LGRAY)
        pdf.set_font("Courier", "", 6.5)
        pdf.set_text_color(*C_DARK)
        pdf.multi_cell(190, 3.2, _safe(show), border=1, fill=True)
        wc = len(text.split())
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(0, 5, f"  {len(text):,} characters | {wc:,} words", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*C_DARK)
        pdf.ln(2)

    def _fields_table(self, pdf, fields):
        # Header
        pdf.set_draw_color(*C_LGRAY)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*C_PRIMARY)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(50, 7, "  Field", border=1, fill=True)
        pdf.cell(95, 7, "  Value", border=1, fill=True)
        pdf.cell(45, 7, "  Confidence", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*C_DARK)

        for i, (name, fd) in enumerate(fields.items()):
            if pdf.get_y() > 270:
                pdf.add_page()
            pdf.set_fill_color(*(C_BLUE_BG if i % 2 == 0 else C_WHITE))
            val, conf = "-", "-"
            if isinstance(fd, dict):
                val = _safe(str(fd.get("value", "-"))[:70])
                c = fd.get("confidence")
                if c is not None:
                    conf = f"{float(c) * 100:.1f}%"
            elif fd is not None:
                val = _safe(str(fd)[:70])

            pdf.set_font("Helvetica", "B", 7.5)
            pdf.cell(50, 6.5, _safe(f"  {name}"), border=1, fill=True)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.cell(95, 6.5, f"  {val}", border=1, fill=True)

            # Color confidence
            if conf != "-":
                cv = float(conf.replace("%", ""))
                if cv >= 80:
                    pdf.set_text_color(*C_GREEN)
                elif cv >= 50:
                    pdf.set_text_color(*C_YELLOW)
                else:
                    pdf.set_text_color(*C_RED)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.cell(45, 6.5, f"  {conf}", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)
        pdf.ln(2)

    def _validation(self, pdf, val_rec):
        rules = val_rec.rule_results or []
        passed = sum(1 for r in rules if r.get("status") == "PASS")
        failed = sum(1 for r in rules if r.get("status") == "FAIL")
        status = val_rec.status or "Unknown"

        # Status banner
        if status == "VALID":
            bg, tc = C_GREEN_BG, C_GREEN
        elif status == "INVALID":
            bg, tc = C_RED_BG, C_RED
        else:
            bg, tc = C_YELLOW_BG, C_YELLOW

        y = pdf.get_y()
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*tc)
        pdf.rect(10, y, 190, 9, "DF")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*tc)
        pdf.set_xy(14, y + 1.5)
        pdf.cell(0, 6, _safe(f"{status}  -  {passed} Passed  |  {failed} Failed  |  {len(rules)} Total"))
        pdf.set_y(y + 12)
        pdf.set_text_color(*C_DARK)

        if not rules:
            return

        # Rules table
        pdf.set_draw_color(*C_LGRAY)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_fill_color(*C_PRIMARY)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(60, 7, "  Rule", border=1, fill=True)
        pdf.cell(22, 7, "  Status", border=1, fill=True)
        pdf.cell(108, 7, "  Message", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*C_DARK)

        for i, r in enumerate(rules):
            if pdf.get_y() > 270:
                pdf.add_page()
            pdf.set_fill_color(*(C_BLUE_BG if i % 2 == 0 else C_WHITE))
            rs = r.get("status", "-")
            rn = _safe(str(r.get("rule_name", "-"))[:33])
            rm = _safe(str(r.get("message", ""))[:68])

            pdf.set_font("Helvetica", "", 7.5)
            pdf.cell(60, 6.5, f"  {rn}", border=1, fill=True)

            if rs == "PASS":
                pdf.set_text_color(*C_GREEN)
            elif rs == "FAIL":
                pdf.set_text_color(*C_RED)
            else:
                pdf.set_text_color(*C_YELLOW)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.cell(22, 6.5, f"  {rs}", border=1, fill=True)

            pdf.set_text_color(*C_DARK)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.cell(108, 6.5, f"  {rm}", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def _anomaly(self, pdf, rec):
        is_a = rec.is_anomaly
        if is_a:
            bg, tc = C_RED_BG, C_RED
            label = "ANOMALY DETECTED - Flagged as statistical outlier"
        else:
            bg, tc = C_GREEN_BG, C_GREEN
            label = "NORMAL - No anomalies detected"

        y = pdf.get_y()
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*tc)
        pdf.rect(10, y, 190, 9, "DF")
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*tc)
        pdf.set_xy(14, y + 1.5)
        pdf.cell(0, 6, _safe(label))
        pdf.set_y(y + 12)
        pdf.set_text_color(*C_DARK)

        self._kv_table(pdf, [
            ("Anomaly Score", f"{rec.anomaly_score:.6f}"),
            ("Decision Function", f"{rec.decision_function_score:.6f}"),
            ("Result", "Outlier (Anomalous)" if is_a else "Inlier (Normal)"),
        ])

        if is_a:
            pdf.set_font("Helvetica", "I", 7.5)
            pdf.set_text_color(*C_RED)
            pdf.multi_cell(0, 3.5, _safe(
                "Warning: Unusual patterns detected. Could indicate data entry errors, "
                "fraudulent content, or an unusual but legitimate document. Manual review recommended."
            ))
            pdf.set_text_color(*C_DARK)
            pdf.ln(2)

    def _duplicates(self, pdf, matches):
        pdf.set_draw_color(*C_LGRAY)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_fill_color(*C_PRIMARY)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(75, 7, "  Matched Document", border=1, fill=True)
        pdf.cell(30, 7, "  Similarity", border=1, fill=True)
        pdf.cell(30, 7, "  Type", border=1, fill=True)
        pdf.cell(55, 7, "  Risk", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*C_DARK)

        for i, m in enumerate(matches[:10]):
            pdf.set_fill_color(*(C_BLUE_BG if i % 2 == 0 else C_WHITE))
            mid = m.matched_document_id if hasattr(m, "matched_document_id") else str(m)
            sc = f"{m.similarity_score:.1%}" if hasattr(m, "similarity_score") else "-"
            dt = m.duplicate_type if hasattr(m, "duplicate_type") else "-"
            risk = "HIGH" if dt == "EXACT" else ("MEDIUM" if dt == "NEAR" else "LOW")

            pdf.set_font("Helvetica", "", 7.5)
            pdf.cell(75, 6.5, _safe(f"  {mid[:30]}"), border=1, fill=True)
            pdf.cell(30, 6.5, f"  {sc}", border=1, fill=True)
            pdf.cell(30, 6.5, f"  {dt}", border=1, fill=True)

            if risk == "HIGH":
                pdf.set_text_color(*C_RED)
            elif risk == "MEDIUM":
                pdf.set_text_color(*C_YELLOW)
            else:
                pdf.set_text_color(*C_GREEN)
            pdf.set_font("Helvetica", "B", 7.5)
            pdf.cell(55, 6.5, f"  {risk}", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)
        pdf.ln(2)

    def _ai(self, pdf, data):
        method = data.get("analysis_method", "unknown")
        self._kv_table(pdf, [("Analysis Method", method)])

        # Summary
        summary = data.get("executive_summary", "")
        if summary:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_PRIMARY)
            pdf.cell(0, 6, "Summary", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, _safe(str(summary)[:2000]))
            pdf.ln(3)

        # Entities
        entities = data.get("entities", {})
        if entities and isinstance(entities, dict):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_PRIMARY)
            pdf.cell(0, 6, "Identified Entities", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)

            for cat, vals in entities.items():
                if not vals:
                    continue
                if pdf.get_y() > 260:
                    pdf.add_page()
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(0, 5, _safe(f"  {cat.replace('_', ' ').title()}"), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 7.5)
                if isinstance(vals, dict):
                    for k, v in vals.items():
                        pdf.cell(0, 4.5, _safe(f"      {k}: {v}"), new_x="LMARGIN", new_y="NEXT")
                elif isinstance(vals, list):
                    for item in vals[:12]:
                        pdf.cell(0, 4.5, _safe(f"      - {str(item)[:90]}"), new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.cell(0, 4.5, _safe(f"      {str(vals)[:150]}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        # Line Items
        items = data.get("line_items", [])
        if items and isinstance(items, list) and len(items) > 0:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_PRIMARY)
            pdf.cell(0, 6, _safe(f"Line Items ({len(items)})"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)

            pdf.set_draw_color(*C_LGRAY)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(*C_PRIMARY)
            pdf.set_text_color(*C_WHITE)
            pdf.cell(10, 6, " #", border=1, fill=True)
            pdf.cell(100, 6, "  Description", border=1, fill=True)
            pdf.cell(25, 6, "  Qty", border=1, fill=True)
            pdf.cell(55, 6, "  Amount", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)

            for idx, item in enumerate(items[:20]):
                if pdf.get_y() > 270:
                    pdf.add_page()
                pdf.set_fill_color(*(C_BLUE_BG if idx % 2 == 0 else C_WHITE))
                if isinstance(item, dict):
                    desc = str(item.get("description", item.get("item", "-")))[:55]
                    qty = str(item.get("quantity", "-"))
                    amt = str(item.get("amount", item.get("total", "-")))
                else:
                    desc, qty, amt = str(item)[:55], "-", "-"

                pdf.set_font("Helvetica", "", 7)
                pdf.cell(10, 5.5, f" {idx+1}", border=1, fill=True)
                pdf.cell(100, 5.5, _safe(f"  {desc}"), border=1, fill=True)
                pdf.cell(25, 5.5, _safe(f"  {qty}"), border=1, fill=True)
                pdf.cell(55, 5.5, _safe(f"  {amt}"), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        # Financial Validation
        fv = data.get("financial_validation", {})
        if fv and isinstance(fv, dict):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_PRIMARY)
            pdf.cell(0, 6, "Financial Validation", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)
            self._kv_table(pdf, [(k, str(v)) for k, v in fv.items()])

        # Risk
        risk = data.get("risk_narrative", "")
        if risk:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_PRIMARY)
            pdf.cell(0, 6, "Risk Assessment", new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(*C_DARK)
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, _safe(str(risk)[:1200]))
            pdf.ln(2)

    def _summary(self, pdf, doc, content_rec, fields, val_rec, anomaly_rec, dups, ai):
        lines = []
        lines.append(f"DOCUMENT: {doc.filename}")
        lines.append(f"TYPE: {doc.document_type or 'Unclassified'}  |  SIZE: {_fmt_bytes(doc.file_size)}")
        lines.append("")

        if content_rec and content_rec.cleaned_text:
            wc = len(content_rec.cleaned_text.split())
            lines.append(f"TEXT: {wc:,} words extracted via OCR")

        lines.append(f"FIELDS: {len(fields)} data field(s) identified")

        if val_rec and val_rec.rule_results:
            r = val_rec.rule_results
            p = sum(1 for x in r if x.get("status") == "PASS")
            lines.append(f"VALIDATION: {val_rec.status} ({p}/{len(r)} passed)")
        else:
            lines.append("VALIDATION: Not performed")

        if anomaly_rec:
            if anomaly_rec.is_anomaly:
                lines.append(f"ANOMALY: FLAGGED (score {anomaly_rec.anomaly_score:.4f}) - Review recommended")
            else:
                lines.append(f"ANOMALY: Normal (score {anomaly_rec.anomaly_score:.4f})")
        else:
            lines.append("ANOMALY: Not checked")

        if dups and len(dups) > 0:
            lines.append(f"DUPLICATES: {len(dups)} match(es) found")
        else:
            lines.append("DUPLICATES: None - document is unique")

        if ai:
            lines.append(f"AI ANALYSIS: Completed ({ai.get('analysis_method', 'unknown')})")
            s = ai.get("executive_summary", "")
            if s:
                lines.append(f"\n{str(s)[:500]}")

        lines.append(f"\nGenerated: {datetime.now(timezone.utc).strftime('%B %d, %Y %H:%M UTC')}")
        lines.append("Processed by Documind Document Intelligence Platform.")

        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*C_DARK)
        pdf.multi_cell(0, 4.5, _safe("\n".join(lines)))
