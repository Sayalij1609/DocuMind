"""
Text preprocessing for document classification.

Prepares raw document text for TF-IDF vectorization.
Preserves financially meaningful tokens (amounts, dates,
invoice numbers, GST, PO references) while removing noise.
"""

import re


def preprocess_for_classification(
    text: str
) -> str:
    """
    Preprocess document text for classification.

    Steps:
    1. Lowercase
    2. Normalize line breaks and whitespace
    3. Remove non-printable characters
    4. Collapse excessive punctuation
    5. Normalize whitespace

    Preserves:
    - Numbers and amounts (e.g. $1,234.56)
    - Dates (e.g. 01/15/2024)
    - Document identifiers (e.g. INV-2024-001)
    - Tax references (GST, VAT, TAX)
    - Currency symbols

    Args:
        text: Raw document text.

    Returns:
        Cleaned text ready for vectorization.
    """

    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Normalize line breaks
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove non-printable characters
    # but keep newlines, tabs, and spaces
    text = re.sub(
        r"[^\x20-\x7E\n\t]",
        " ",
        text
    )

    # Collapse repeated punctuation
    # (e.g. "---" → "-", "..." → ".")
    text = re.sub(
        r"([^\w\s])\1{2,}",
        r"\1",
        text
    )

    # Collapse multiple spaces into one
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Collapse excessive newlines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()
