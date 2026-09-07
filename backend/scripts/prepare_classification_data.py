"""
Nexora — Dataset Preparation Script
=====================================

Converts the Kaggle "Company Documents" CSV dataset
into Nexora's training directory structure.

Dataset: https://www.kaggle.com/datasets/ (search "Company Documents")
The CSV has columns: text, label, word_count

Usage:
------
1. Download the dataset CSV from Kaggle
2. Place it in data/ directory
3. Run this script:

   cd backend
   python scripts/prepare_classification_data.py --csv ../data/company_documents.csv --output ../data/classification

The script will create:
   data/classification/
   ├── invoice/
   │   ├── doc_001.txt
   │   ├── doc_002.txt
   │   └── ...
   ├── purchase_order/
   │   ├── doc_001.txt
   │   └── ...
   └── other/
       ├── doc_001.txt
       └── ...

If your CSV has different column names, use --text-col and --label-col.
"""

import argparse
import csv
import os
import sys
from pathlib import Path


# =========================================================
# Class mapping: Dataset labels → Nexora classes
# =========================================================

DEFAULT_LABEL_MAP = {
    # Direct matches
    "invoice": "invoice",
    "invoices": "invoice",
    "receipt": "receipt",
    "receipts": "receipt",
    "purchase order": "purchase_order",
    "purchase_order": "purchase_order",
    "bank statement": "bank_statement",
    "bank_statement": "bank_statement",
    "insurance": "insurance",

    # Common dataset-specific labels → other
    "shipping order": "other",
    "shipping_order": "other",
    "inventory report": "other",
    "inventory_report": "other",
    "letter": "other",
    "memo": "other",
    "email": "other",
    "report": "other",
    "resume": "other",
    "scientific_report": "other",
    "advertisement": "other",
    "budget": "other",
    "form": "other",
    "file_folder": "other",
    "handwritten": "other",
    "news_article": "other",
    "presentation": "other",
    "questionnaire": "other",
    "specification": "other",
}


def normalize_label(
    raw_label: str,
    label_map: dict[str, str]
) -> str:
    """Map a raw dataset label to a Nexora class."""

    key = raw_label.strip().lower()

    if key in label_map:
        return label_map[key]

    return "other"


def detect_csv_columns(
    headers: list[str]
) -> tuple[str, str]:
    """
    Auto-detect text and label column names
    from the CSV headers.
    """

    text_candidates = [
        "text", "content", "extracted_text",
        "document_text", "ocr_text", "body"
    ]

    label_candidates = [
        "label", "class", "category",
        "document_type", "type", "doc_type"
    ]

    text_col = None
    label_col = None

    lower_headers = [
        h.strip().lower() for h in headers
    ]

    for candidate in text_candidates:
        if candidate in lower_headers:
            idx = lower_headers.index(candidate)
            text_col = headers[idx]
            break

    for candidate in label_candidates:
        if candidate in lower_headers:
            idx = lower_headers.index(candidate)
            label_col = headers[idx]
            break

    return text_col, label_col


def prepare_dataset(
    csv_path: str,
    output_dir: str,
    text_col: str | None = None,
    label_col: str | None = None,
    min_text_length: int = 20,
    label_map: dict[str, str] | None = None
):
    """
    Read a CSV file and create the classification
    directory structure with one .txt file per document.
    """

    csv_path = Path(csv_path)
    output_dir = Path(output_dir)

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    if label_map is None:
        label_map = DEFAULT_LABEL_MAP

    # -------------------------------------------------
    # Read CSV and detect columns
    # -------------------------------------------------

    # Try different encodings
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(csv_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                rows = list(reader)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        print("Error: Could not decode CSV file")
        sys.exit(1)

    print(f"CSV loaded: {len(rows)} rows")
    print(f"Columns: {headers}")

    # -------------------------------------------------
    # Auto-detect or validate columns
    # -------------------------------------------------

    if text_col is None or label_col is None:

        auto_text, auto_label = detect_csv_columns(
            headers
        )

        if text_col is None:
            text_col = auto_text

        if label_col is None:
            label_col = auto_label

    if text_col is None:
        print(
            "Error: Could not detect text column. "
            f"Available: {headers}"
        )
        print("Use --text-col to specify manually.")
        sys.exit(1)

    if label_col is None:
        print(
            "Error: Could not detect label column. "
            f"Available: {headers}"
        )
        print("Use --label-col to specify manually.")
        sys.exit(1)

    print(f"Text column: '{text_col}'")
    print(f"Label column: '{label_col}'")

    # -------------------------------------------------
    # Process rows and write text files
    # -------------------------------------------------

    class_counts: dict[str, int] = {}
    skipped = 0

    for row in rows:

        raw_text = row.get(text_col, "")
        raw_label = row.get(label_col, "")

        if not raw_text or not raw_label:
            skipped += 1
            continue

        text = raw_text.strip()

        if len(text) < min_text_length:
            skipped += 1
            continue

        nexora_class = normalize_label(
            raw_label, label_map
        )

        class_dir = output_dir / nexora_class

        class_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        count = class_counts.get(
            nexora_class, 0
        ) + 1

        class_counts[nexora_class] = count

        filename = f"doc_{count:04d}.txt"

        file_path = class_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

    # -------------------------------------------------
    # Summary
    # -------------------------------------------------

    print()
    print("=" * 50)
    print("Dataset prepared successfully!")
    print("=" * 50)
    print(f"Output directory: {output_dir}")
    print(f"Skipped (empty/short): {skipped}")
    print()

    total = 0

    for class_name in sorted(class_counts.keys()):

        count = class_counts[class_name]
        total += count

        print(f"  {class_name}: {count} documents")

    print(f"\n  Total: {total} documents")
    print()


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Prepare classification training data "
            "from a CSV file."
        )
    )

    parser.add_argument(
        "--csv",
        required=True,
        help="Path to the CSV file"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for classification data"
    )

    parser.add_argument(
        "--text-col",
        default=None,
        help=(
            "Name of the text column "
            "(auto-detected if not specified)"
        )
    )

    parser.add_argument(
        "--label-col",
        default=None,
        help=(
            "Name of the label column "
            "(auto-detected if not specified)"
        )
    )

    parser.add_argument(
        "--min-length",
        type=int,
        default=20,
        help=(
            "Minimum text length to include "
            "(default: 20)"
        )
    )

    args = parser.parse_args()

    prepare_dataset(
        csv_path=args.csv,
        output_dir=args.output,
        text_col=args.text_col,
        label_col=args.label_col,
        min_text_length=args.min_length
    )


if __name__ == "__main__":
    main()
