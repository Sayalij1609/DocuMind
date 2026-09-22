"""
OCR Post-Processing Correction Service.

Uses Groq LLM to fix common OCR artifacts (broken words,
character substitutions, garbled punctuation) while preserving
numerical values and document formatting.

Falls back to the original text if LLM is unavailable.
"""

import logging
import re
from typing import Optional

import httpx

from app.core.config import settings
from app.services.ai_analysis_service import (
    get_runtime_api_key,
)

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TIMEOUT = 45.0

OCR_CORRECTION_PROMPT = """You are an OCR post-processing specialist. Your ONLY job is to fix OCR errors in the following extracted text.

RULES:
1. Fix common OCR character substitutions: 0↔O, 1↔l↔I, 5↔S, 8↔B, rn↔m, cl↔d
2. Fix broken/split words that should be joined
3. Fix garbled punctuation and spacing
4. Preserve ALL numerical values exactly — do NOT change amounts, dates, or IDs
5. Preserve the original layout/structure as much as possible
6. Do NOT add, remove, or rephrase any content
7. Do NOT add explanations, headers, or markdown formatting
8. Return ONLY the corrected text, nothing else

OCR TEXT:
{text}

CORRECTED TEXT:"""


class OCRCorrectionService:
    """Correct OCR artifacts using LLM or rule-based fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or get_runtime_api_key()
            or settings.groq_api_key
            or None
        )
        self.model = (
            model
            or settings.groq_model
            or "qwen/qwen3.8-27b"
        )

    def correct_text(
        self,
        raw_ocr_text: str,
        document_type: Optional[str] = None,
    ) -> str:
        """
        Correct OCR text using LLM with rule-based fallback.

        Args:
            raw_ocr_text: The raw OCR output text.
            document_type: Optional type hint for context.

        Returns:
            Corrected text string.
        """
        if not raw_ocr_text or not raw_ocr_text.strip():
            return raw_ocr_text or ""

        # Skip very short texts (likely already clean)
        if len(raw_ocr_text.strip()) < 20:
            return raw_ocr_text

        # Try LLM correction
        if self.api_key:
            try:
                corrected = self._llm_correct(
                    raw_ocr_text, document_type
                )
                if corrected and len(corrected.strip()) > 10:
                    logger.info(
                        "OCR correction via LLM: %d → %d chars",
                        len(raw_ocr_text),
                        len(corrected),
                    )
                    return corrected
            except Exception:
                logger.exception(
                    "LLM OCR correction failed, "
                    "falling back to rules"
                )

        # Rule-based fallback
        corrected = self._rule_based_correct(raw_ocr_text)
        logger.info(
            "OCR correction via rules: %d → %d chars",
            len(raw_ocr_text),
            len(corrected),
        )
        return corrected

    def _llm_correct(
        self,
        text: str,
        document_type: Optional[str] = None,
    ) -> Optional[str]:
        """Send text to Groq for LLM-based OCR correction."""

        # Truncate very long texts to avoid token limits
        max_chars = 8000
        truncated = text[:max_chars] if len(text) > max_chars else text

        prompt = OCR_CORRECTION_PROMPT.format(text=truncated)

        if document_type:
            prompt = (
                f"[Document type: {document_type}]\n\n"
                + prompt
            )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.1,
            "max_tokens": max_chars + 500,
        }

        with httpx.Client(timeout=GROQ_TIMEOUT) as client:
            response = client.post(
                GROQ_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        # Strip any thinking tags from Qwen models
        content = re.sub(
            r"<think>.*?</think>",
            "",
            content,
            flags=re.DOTALL,
        ).strip()

        # If the response starts with common prefixes, strip them
        for prefix in [
            "CORRECTED TEXT:",
            "Here is the corrected text:",
            "Corrected text:",
        ]:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()

        return content if content else None

    def _rule_based_correct(self, text: str) -> str:
        """Apply deterministic regex-based OCR corrections."""

        corrected = text

        # Fix common OCR ligature/character issues
        # rn → m (when in common words)
        common_rn_words = {
            "governrnent": "government",
            "docurnent": "document",
            "payrnent": "payment",
            "staternent": "statement",
            "cornpany": "company",
            "arnount": "amount",
            "nurnber": "number",
            "rnanager": "manager",
            "cornmerce": "commerce",
            "inforrnation": "information",
            "environrnent": "environment",
            "departrnent": "department",
            "investrnent": "investment",
            "developrnent": "development",
            "rnanagement": "management",
            "requirernent": "requirement",
            "achievernent": "achievement",
            "agreernent": "agreement",
            "assessrnent": "assessment",
            "cornmunication": "communication",
            "cornpliance": "compliance",
        }

        for wrong, right in common_rn_words.items():
            corrected = re.sub(
                re.escape(wrong),
                right,
                corrected,
                flags=re.IGNORECASE,
            )

        # Fix broken words with extra spaces in the middle
        # e.g., "In vo ice" → "Invoice"
        corrected = re.sub(
            r"\b(In)\s+(vo)\s+(ice)\b",
            "Invoice",
            corrected,
            flags=re.IGNORECASE,
        )

        # Fix l/1 confusion in common contexts
        # "Tota1" → "Total"
        corrected = re.sub(
            r"\bTota1\b", "Total", corrected
        )
        corrected = re.sub(
            r"\bInvo1ce\b", "Invoice", corrected,
            flags=re.IGNORECASE,
        )

        # Remove excessive whitespace (but preserve newlines)
        corrected = re.sub(r"[ \t]{3,}", "  ", corrected)

        # Fix garbled punctuation sequences
        corrected = re.sub(r"[,]{2,}", ",", corrected)
        corrected = re.sub(r"[\.]{4,}", "...", corrected)

        return corrected


def get_ocr_correction_service(
    api_key: Optional[str] = None,
) -> OCRCorrectionService:
    """Factory function for OCR correction service."""
    return OCRCorrectionService(api_key=api_key)
