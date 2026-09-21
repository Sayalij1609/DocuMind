"""
AI Analysis Service — Groq LLM + Intelligent Local Fallback.

Provides high-quality semantic document analysis including:
  • Executive Summary
  • Semantic Entity Mapping
  • Line Items / Table Parsing
  • Arithmetic Validation
  • Risk & Anomaly Narrative
  • Document Q&A (interactive)

When a Groq API key is available, uses the Groq Chat
Completions API (llama-3.3-70b-versatile). Otherwise,
automatically falls back to a capable local heuristic
engine so processing never fails.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Groq API Constants
# --------------------------------------------------
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT = 60.0  # seconds


class AIAnalysisService:
    """Hybrid AI analysis: Groq LLM → local fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or settings.groq_api_key
            or None
        )
        self.model = (
            model
            or settings.groq_model
            or "llama-3.3-70b-versatile"
        )

    # ==========================================
    # Public: Full Document Analysis
    # ==========================================

    def analyze_document(
        self,
        document_text: str,
        document_type: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run complete semantic analysis on a document.

        Returns a dict with keys:
          executive_summary, document_type,
          entities, relationships,
          line_items, financial_validation,
          risk_narrative, analysis_method,
          analyzed_at
        """

        if not document_text or not document_text.strip():
            return self._empty_analysis_result()

        # Try Groq first
        if self.api_key:
            try:
                result = self._analyze_with_groq(
                    document_text,
                    document_type,
                    filename,
                )
                result["analysis_method"] = "groq_llm"
                result["analyzed_at"] = (
                    datetime.utcnow().isoformat()
                )
                logger.info(
                    "AI analysis completed via Groq "
                    "for: %s",
                    filename or "unknown",
                )
                return result

            except Exception:
                logger.exception(
                    "Groq analysis failed, "
                    "falling back to local engine"
                )

        # Local fallback
        result = self._analyze_locally(
            document_text,
            document_type,
            filename,
        )
        result["analysis_method"] = "local_heuristic"
        result["analyzed_at"] = (
            datetime.utcnow().isoformat()
        )
        logger.info(
            "AI analysis completed via local "
            "heuristic for: %s",
            filename or "unknown",
        )
        return result

    # ==========================================
    # Public: Document Q&A
    # ==========================================

    def ask_question(
        self,
        document_text: str,
        question: str,
        document_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Answer a user question about a document.

        Returns { answer, citations, method }.
        """

        if not self.api_key:
            return {
                "answer": (
                    "AI Q&A requires a Groq API key. "
                    "Please configure your API key in "
                    "Settings → AI Configuration to "
                    "enable document question answering."
                ),
                "citations": [],
                "method": "unavailable",
            }

        try:
            return self._qa_with_groq(
                document_text,
                question,
                document_type,
            )
        except Exception:
            logger.exception(
                "Groq Q&A failed for question: %s",
                question[:80],
            )
            return {
                "answer": (
                    "Sorry, I was unable to process "
                    "your question right now. Please "
                    "try again in a moment."
                ),
                "citations": [],
                "method": "error",
            }

    # ==========================================
    # Groq LLM: Full Analysis
    # ==========================================

    def _analyze_with_groq(
        self,
        text: str,
        doc_type: Optional[str],
        filename: Optional[str],
    ) -> dict[str, Any]:

        system_prompt = self._build_analysis_system_prompt()
        user_prompt = self._build_analysis_user_prompt(
            text, doc_type, filename
        )

        response = self._call_groq(
            system_prompt, user_prompt
        )

        # Parse JSON from response
        return self._parse_groq_json(response)

    # ==========================================
    # Groq LLM: Q&A
    # ==========================================

    def _qa_with_groq(
        self,
        text: str,
        question: str,
        doc_type: Optional[str],
    ) -> dict[str, Any]:

        system_prompt = (
            "You are DocuMind AI, an expert document "
            "analysis assistant. You answer questions "
            "about business documents with precise, "
            "grounded answers. Always cite specific "
            "values, dates, or sections from the "
            "document text. If you cannot find the "
            "answer in the document, say so honestly.\n\n"
            "Respond in JSON format:\n"
            '{"answer": "...", "citations": ["..."]}'
        )

        user_prompt = (
            f"Document Type: {doc_type or 'Unknown'}\n\n"
            f"--- DOCUMENT TEXT ---\n{text[:6000]}\n"
            f"--- END ---\n\n"
            f"Question: {question}"
        )

        response = self._call_groq(
            system_prompt, user_prompt
        )

        try:
            parsed = self._parse_groq_json(response)
            return {
                "answer": parsed.get(
                    "answer",
                    response
                ),
                "citations": parsed.get(
                    "citations", []
                ),
                "method": "groq_llm",
            }
        except Exception:
            return {
                "answer": response,
                "citations": [],
                "method": "groq_llm",
            }

    # ==========================================
    # Groq HTTP Client
    # ==========================================

    def _call_groq(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Synchronous call to Groq Chat API."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"},
        }

        with httpx.Client(
            timeout=GROQ_TIMEOUT
        ) as client:
            resp = client.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()

        data = resp.json()
        return (
            data["choices"][0]["message"]["content"]
        )

    # ==========================================
    # Prompt Builders
    # ==========================================

    def _build_analysis_system_prompt(self) -> str:
        return (
            "You are DocuMind AI, an expert document "
            "analysis engine for business documents "
            "(invoices, receipts, purchase orders, "
            "bank statements, insurance documents, "
            "application forms, bills, business "
            "reports, delivery challans).\n\n"
            "Analyze the document text and return a "
            "JSON object with EXACTLY these keys:\n\n"
            "1. \"executive_summary\": A 2-3 sentence "
            "friendly, professional summary of the "
            "document highlighting who issued it, "
            "to whom, key dates, purpose, and "
            "financial obligations.\n\n"
            "2. \"document_type\": The precise "
            "category (invoice, receipt, purchase_order, "
            "bank_statement, insurance, application_form, "
            "bill, business_report, delivery_challan, "
            "other).\n\n"
            "3. \"entities\": An object with these "
            "sub-keys:\n"
            "   - \"parties\": [{\"name\": ..., "
            "\"role\": \"vendor\"|\"customer\"|"
            "\"issuer\"|\"recipient\", "
            "\"address\": ..., \"tax_id\": ..., "
            "\"contact\": ...}]\n"
            "   - \"identifiers\": [{\"type\": "
            "\"invoice_number\"|\"po_number\"|"
            "\"account_number\"|\"policy_number\"|"
            "\"challan_number\", \"value\": ...}]\n"
            "   - \"dates\": [{\"type\": "
            "\"issue_date\"|\"due_date\"|"
            "\"delivery_date\"|\"period\", "
            "\"value\": ...}]\n"
            "   - \"financials\": {\"subtotal\": ..., "
            "\"tax\": ..., \"discount\": ..., "
            "\"total\": ..., \"currency\": "
            "\"INR\" (or detected currency symbol, "
            "prioritize INR / ₹ / Rupees)}\n\n"
            "4. \"relationships\": An array of "
            "[{\"entity\": \"...\", \"role\": \"...\"}] "
            "mappings for display (e.g., "
            "{\"entity\": \"ABC Corp\", "
            "\"role\": \"Vendor\"}).\n\n"
            "5. \"line_items\": An array of "
            "[{\"description\": ..., \"quantity\": ..., "
            "\"unit_price\": ..., \"amount\": ...}].\n\n"
            "6. \"financial_validation\": "
            "{\"subtotal\": ..., \"tax\": ..., "
            "\"discount\": ..., \"computed_total\": ..., "
            "\"stated_total\": ..., "
            "\"is_valid\": true|false, "
            "\"discrepancy\": ..., \"notes\": ...}\n\n"
            "7. \"risk_narrative\": A plain-English "
            "explanation of any anomalies, unusual "
            "charges, missing fields, expired dates, "
            "or compliance issues. Say \"No issues "
            "detected\" if everything looks normal.\n\n"
            "Return ONLY valid JSON. No markdown "
            "fencing. Extract as many entities as you "
            "can find. Use null for fields you cannot "
            "determine."
        )

    def _build_analysis_user_prompt(
        self,
        text: str,
        doc_type: Optional[str],
        filename: Optional[str],
    ) -> str:

        header = ""
        if filename:
            header += f"Filename: {filename}\n"
        if doc_type:
            header += (
                f"Pre-classified Type: {doc_type}\n"
            )

        # Truncate to ~6000 chars for token limits
        truncated = text[:6000]

        return (
            f"{header}\n"
            f"--- DOCUMENT TEXT ---\n"
            f"{truncated}\n"
            f"--- END ---\n\n"
            f"Analyze this document completely."
        )

    # ==========================================
    # JSON Parser (robust)
    # ==========================================

    def _parse_groq_json(
        self, raw: str
    ) -> dict[str, Any]:
        """Parse JSON from Groq response,
        handling markdown fences."""

        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\s*\n?",
                "",
                cleaned,
            )
            cleaned = re.sub(
                r"\n?```\s*$", "", cleaned
            )

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            match = re.search(
                r"\{.*\}",
                cleaned,
                re.DOTALL,
            )
            if match:
                return json.loads(match.group())
            raise

    # ==========================================
    # Local Heuristic Fallback
    # ==========================================

    def _analyze_locally(
        self,
        text: str,
        doc_type: Optional[str],
        filename: Optional[str],
    ) -> dict[str, Any]:
        """
        Rule-based analysis when no LLM is available.
        Uses regex patterns for common fields.
        """

        text_lower = text.lower()

        # Determine document type
        detected_type = doc_type or "unknown"
        if detected_type == "unknown":
            type_keywords = {
                "invoice": [
                    "invoice", "inv-", "bill to",
                    "due date", "invoice number",
                ],
                "receipt": [
                    "receipt", "paid", "thank you",
                    "transaction",
                ],
                "purchase_order": [
                    "purchase order", "p.o.",
                    "po number", "ship to",
                ],
                "bank_statement": [
                    "bank statement", "account summary",
                    "opening balance", "closing balance",
                ],
                "delivery_challan": [
                    "challan", "delivery note",
                    "dispatch",
                ],
            }
            for dtype, kws in type_keywords.items():
                if any(kw in text_lower for kw in kws):
                    detected_type = dtype
                    break

        # Extract amounts
        amounts = re.findall(
            r"[\$₹€£¥]?\s*[\d,]+\.?\d*",
            text,
        )
        numeric_amounts = []
        for a in amounts:
            cleaned = re.sub(r"[^\d.]", "", a)
            if cleaned and "." in cleaned:
                try:
                    numeric_amounts.append(
                        float(cleaned)
                    )
                except ValueError:
                    pass
            elif cleaned:
                try:
                    val = float(cleaned)
                    if val > 0:
                        numeric_amounts.append(val)
                except ValueError:
                    pass

        total = (
            max(numeric_amounts)
            if numeric_amounts
            else None
        )

        # Extract dates
        date_patterns = [
            r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
            r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|"
            r"Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*"
            r"\s+\d{2,4}",
        ]
        dates_found = []
        for pat in date_patterns:
            dates_found.extend(
                re.findall(pat, text, re.IGNORECASE)
            )

        # Extract identifiers
        inv_match = re.search(
            r"(?:invoice|inv|bill)\s*(?:#|no\.?|"
            r"number)?\s*[:.]?\s*([A-Z0-9][\w-]{2,})",
            text,
            re.IGNORECASE,
        )
        po_match = re.search(
            r"(?:purchase\s*order|p\.?o\.?)\s*"
            r"(?:#|no\.?|number)?\s*[:.]?\s*"
            r"([A-Z0-9][\w-]{2,})",
            text,
            re.IGNORECASE,
        )

        # Build relationships
        relationships = []
        if inv_match:
            relationships.append({
                "entity": inv_match.group(1),
                "role": "Invoice Number",
            })
        if po_match:
            relationships.append({
                "entity": po_match.group(1),
                "role": "PO Number",
            })
        if total is not None:
            relationships.append({
                "entity": f"₹{total:,.2f}",
                "role": "Total Amount",
            })
        if dates_found:
            relationships.append({
                "entity": dates_found[0],
                "role": "Primary Date",
            })

        # Build summary
        parts = [
            f"This is a {detected_type.replace('_', ' ')} document"
        ]
        if filename:
            parts[0] += f" ({filename})"
        parts[0] += "."
        if total is not None:
            parts.append(
                f"The total amount identified is "
                f"₹{total:,.2f}."
            )
        if dates_found:
            parts.append(
                f"Key dates found: "
                f"{', '.join(dates_found[:3])}."
            )

        summary = " ".join(parts)

        # Financial validation
        fin_validation = {
            "subtotal": None,
            "tax": None,
            "discount": None,
            "computed_total": None,
            "stated_total": total,
            "is_valid": None,
            "discrepancy": None,
            "notes": (
                "Local heuristic — detailed "
                "arithmetic validation requires "
                "AI analysis. Configure a Groq "
                "API key for full validation."
            ),
        }

        return {
            "executive_summary": summary,
            "document_type": detected_type,
            "entities": {
                "parties": [],
                "identifiers": [
                    {
                        "type": "invoice_number",
                        "value": (
                            inv_match.group(1)
                            if inv_match
                            else None
                        ),
                    },
                    {
                        "type": "po_number",
                        "value": (
                            po_match.group(1)
                            if po_match
                            else None
                        ),
                    },
                ],
                "dates": [
                    {"type": "detected", "value": d}
                    for d in dates_found[:5]
                ],
                "financials": {
                    "subtotal": None,
                    "tax": None,
                    "discount": None,
                    "total": total,
                    "currency": (
                        "INR"
                        if "₹" in text or "rs" in text.lower() or "inr" in text.lower()
                        else "USD"
                        if "$" in text
                        else "INR"
                    ),
                },
            },
            "relationships": relationships,
            "line_items": [],
            "financial_validation": fin_validation,
            "risk_narrative": (
                "Local heuristic analysis completed. "
                "For detailed risk assessment, "
                "configure a Groq API key."
            ),
        }

    # ==========================================
    # Empty Result
    # ==========================================

    def _empty_analysis_result(
        self,
    ) -> dict[str, Any]:
        return {
            "executive_summary": (
                "No document text available for "
                "analysis."
            ),
            "document_type": "unknown",
            "entities": {
                "parties": [],
                "identifiers": [],
                "dates": [],
                "financials": {},
            },
            "relationships": [],
            "line_items": [],
            "financial_validation": {},
            "risk_narrative": "No text to analyze.",
            "analysis_method": "none",
            "analyzed_at": (
                datetime.utcnow().isoformat()
            ),
        }


# --------------------------------------------------
# Runtime API Key Management
# --------------------------------------------------

_runtime_api_key: Optional[str] = None


def set_runtime_api_key(key: str) -> None:
    global _runtime_api_key
    _runtime_api_key = key


def get_runtime_api_key() -> Optional[str]:
    return _runtime_api_key


def get_ai_service(
    api_key: Optional[str] = None,
) -> AIAnalysisService:
    """Factory that respects runtime + env key."""
    effective_key = (
        api_key
        or get_runtime_api_key()
        or settings.groq_api_key
    )
    return AIAnalysisService(api_key=effective_key)
