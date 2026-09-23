"""
================================================================================
NEXORA — RAW DATA CONVERTER
================================================================================
Converts existing raw data in data/ folder into training-ready .txt files.

Handles:
  1. HTML → text  (Balance Sheets, Income Statements, Cash Flow, Others)
  2. JPG → text   (Bank Statements, Salary Slips, ITR/Form16, Checks)
  3. CSV → text   (bankstatements.csv, data_synthetic.csv)

Usage: python scripts/convert_raw_data.py
================================================================================
"""

import os
import re
import sys
import csv
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA = BASE_DIR / "data"
CLASSIFICATION = RAW_DATA / "classification"

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: count existing docs in a folder
# ─────────────────────────────────────────────────────────────────────────────
def next_doc_index(folder: Path) -> int:
    """Returns the next available doc index in a category folder."""
    existing = sorted(folder.glob("doc_*.txt"))
    if not existing:
        return 1
    last = existing[-1].stem  # e.g. "doc_0830"
    try:
        return int(last.split("_")[1]) + 1
    except (IndexError, ValueError):
        return len(existing) + 1


def clean_text(text: str, max_bytes: int = 2000) -> str:
    """Normalize text to lowercase OCR-like format."""
    # Remove excessive whitespace and normalize
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)  # collapse whitespace
    text = re.sub(r'[^\x20-\x7e\n]', '', text)  # ASCII only
    # Restore some line breaks for readability
    text = text.replace('. ', '.\n')
    # Truncate to max size
    if len(text.encode('utf-8')) > max_bytes:
        text = text[:max_bytes]
    return text


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERTER 1: HTML → TEXT
# ═══════════════════════════════════════════════════════════════════════════════
def convert_html_folder(src_name: str, dst_category: str):
    """Convert a folder of HTML files to plain text classification data."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("  [ERROR] beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        return 0

    src = RAW_DATA / src_name
    dst = CLASSIFICATION / dst_category
    dst.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        print(f"  [SKIP] Source folder not found: {src}")
        return 0

    html_files = sorted(src.glob("*.html"))
    if not html_files:
        print(f"  [SKIP] No HTML files in: {src}")
        return 0

    idx = next_doc_index(dst)
    converted = 0

    for html_file in html_files:
        try:
            # Read HTML with fallback encodings
            try:
                raw = html_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                raw = html_file.read_text(encoding="latin-1", errors="ignore")

            soup = BeautifulSoup(raw, "html.parser")

            # Extract table text (most financial HTML is tabular)
            tables = soup.find_all("table")
            if tables:
                parts = []
                for table in tables:
                    rows = table.find_all("tr")
                    for row in rows:
                        cells = row.find_all(["td", "th"])
                        cell_text = " ".join(
                            c.get_text(strip=True) for c in cells
                        )
                        if cell_text.strip():
                            parts.append(cell_text)
                text = "\n".join(parts)
            else:
                text = soup.get_text(separator=" ", strip=True)

            text = clean_text(text)

            # Skip very short extractions (likely empty tables)
            if len(text) < 50:
                continue

            out_file = dst / f"doc_{idx:04d}.txt"
            out_file.write_text(text, encoding="utf-8")
            idx += 1
            converted += 1

        except Exception as e:
            print(f"  [WARN] Failed to convert {html_file.name}: {e}")
            continue

    return converted


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERTER 2: JPG → TEXT (OCR)
# ═══════════════════════════════════════════════════════════════════════════════
def convert_jpg_folder(src_name: str, dst_category: str):
    """Convert a folder of JPG images to text using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        print("  [ERROR] pytesseract or Pillow not installed.")
        print("          Run: pip install pytesseract Pillow")
        print("          Also install Tesseract: https://github.com/tesseract-ocr/tesseract")
        return 0

    src = RAW_DATA / src_name
    dst = CLASSIFICATION / dst_category
    dst.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        print(f"  [SKIP] Source folder not found: {src}")
        return 0

    jpg_files = sorted(src.glob("*.jpg"))
    if not jpg_files:
        print(f"  [SKIP] No JPG files in: {src}")
        return 0

    # Test if Tesseract is actually available
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        print("  [ERROR] Tesseract OCR engine not found on system PATH.")
        print("          Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("          After install, add to PATH or set:")
        print("          pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'")
        return 0

    idx = next_doc_index(dst)
    converted = 0

    for jpg_file in jpg_files:
        try:
            img = Image.open(jpg_file)

            # Convert to grayscale for better OCR
            if img.mode != "L":
                img = img.convert("L")

            # OCR with English language
            text = pytesseract.image_to_string(img, lang="eng")
            text = clean_text(text)

            # Skip if OCR produced too little text
            if len(text) < 30:
                print(f"  [SKIP] Too little text from: {jpg_file.name}")
                continue

            out_file = dst / f"doc_{idx:04d}.txt"
            out_file.write_text(text, encoding="utf-8")
            idx += 1
            converted += 1

        except Exception as e:
            print(f"  [WARN] Failed to OCR {jpg_file.name}: {e}")
            continue

    return converted


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERTER 3: CSV → TEXT
# ═══════════════════════════════════════════════════════════════════════════════
def convert_bankstatements_csv():
    """Convert bankstatements.csv into bank_statement text files."""
    csv_path = RAW_DATA / "bankstatements.csv"
    dst = CLASSIFICATION / "bank_statement"
    dst.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        print(f"  [SKIP] File not found: {csv_path}")
        return 0

    try:
        import pandas as pd
    except ImportError:
        print("  [ERROR] pandas not installed. Run: pip install pandas")
        return 0

    df = pd.read_csv(csv_path)
    idx = next_doc_index(dst)
    converted = 0

    # Group transactions into statement chunks of 10-20 rows
    chunk_size = 15
    bank_names = [
        "state bank of india", "hdfc bank", "icici bank", "axis bank",
        "punjab national bank", "bank of baroda", "kotak mahindra bank",
    ]
    account_nums = [
        "38912076543", "50100234567", "912345678901", "77012345678",
        "6012345890", "45678912345", "9876543210",
    ]

    import random
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        if len(chunk) < 3:
            continue

        bank = random.choice(bank_names)
        acct = random.choice(account_nums)

        lines = [
            f"bank statement {bank}",
            f"account number {acct}",
            f"statement period {chunk.iloc[0]['date']} to {chunk.iloc[-1]['date']}",
            f"opening balance {chunk.iloc[0].get('balance', 0)}",
        ]

        for _, row in chunk.iterrows():
            dr_cr = str(row.get("DrCr", "")).lower()
            mode = str(row.get("mode", "")).lower()
            name = str(row.get("name", "")).lower()
            amount = row.get("amount", 0)
            balance = row.get("balance", 0)
            date = row.get("date", "")

            txn_type = "debit" if dr_cr == "db" else "credit"
            lines.append(
                f"{date} {txn_type} {amount} balance {balance} {mode} {name}"
            )

        lines.append(f"closing balance {chunk.iloc[-1].get('balance', 0)}")
        lines.append(f"total transactions {len(chunk)}")

        text = "\n".join(lines).lower().strip()
        out_file = dst / f"doc_{idx:04d}.txt"
        out_file.write_text(text, encoding="utf-8")
        idx += 1
        converted += 1

    return converted


def convert_insurance_csv():
    """Convert data_synthetic.csv into insurance_policy text files."""
    csv_path = RAW_DATA / "data_synthetic.csv"
    dst = CLASSIFICATION / "insurance_policy"
    dst.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        print(f"  [SKIP] File not found: {csv_path}")
        return 0

    try:
        import pandas as pd
    except ImportError:
        print("  [ERROR] pandas not installed.")
        return 0

    df = pd.read_csv(csv_path)
    idx = next_doc_index(dst)
    converted = 0

    # Limit to 800 extra samples to keep class balance reasonable
    max_samples = 800

    for i, (_, row) in enumerate(df.iterrows()):
        if i >= max_samples:
            break

        try:
            text = (
                f"insurance policy record\n"
                f"customer id {row.get('Customer ID', '')}\n"
                f"age {row.get('Age', '')} gender {row.get('Gender', '')}\n"
                f"marital status {row.get('Marital Status', '')}\n"
                f"occupation {row.get('Occupation', '')}\n"
                f"income level {row.get('Income Level', '')}\n"
                f"education {row.get('Education Level', '')}\n"
                f"location {row.get('Geographic Information', '')} {row.get('Location', '')}\n"
                f"policy type {row.get('Policy Type', '')}\n"
                f"insurance products owned {row.get('Insurance Products Owned', '')}\n"
                f"coverage amount {row.get('Coverage Amount', '')}\n"
                f"premium amount {row.get('Premium Amount', '')}\n"
                f"deductible {row.get('Deductible', '')}\n"
                f"policy start date {row.get('Policy Start Date', '')}\n"
                f"policy renewal date {row.get('Policy Renewal Date', '')}\n"
                f"claim history {row.get('Claim History', '')}\n"
                f"risk profile {row.get('Risk Profile', '')}\n"
                f"previous claims {row.get('Previous Claims History', '')}\n"
                f"credit score {row.get('Credit Score', '')}\n"
                f"driving record {row.get('Driving Record', '')}\n"
                f"life events {row.get('Life Events', '')}\n"
                f"segmentation {row.get('Segmentation Group', '')}\n"
            ).lower().strip()

            out_file = dst / f"doc_{idx:04d}.txt"
            out_file.write_text(text, encoding="utf-8")
            idx += 1
            converted += 1

        except Exception as e:
            continue

    return converted


def convert_insurance_claims_csv():
    """Convert insurance_dataset.csv into insurance_policy text files."""
    csv_path = RAW_DATA / "insurance_dataset.csv"
    dst = CLASSIFICATION / "insurance_policy"
    dst.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        print(f"  [SKIP] File not found: {csv_path}")
        return 0

    try:
        import pandas as pd
    except ImportError:
        return 0

    df = pd.read_csv(csv_path)
    idx = next_doc_index(dst)
    converted = 0
    max_samples = 500

    import random
    policy_types = [
        "term life insurance", "health insurance", "motor insurance",
        "endowment plan", "unit linked plan", "whole life insurance",
    ]

    for i, (_, row) in enumerate(df.iterrows()):
        if i >= max_samples:
            break
        try:
            text = (
                f"insurance claim record\n"
                f"policyholder age {row.get('Age', '')}\n"
                f"gender {row.get('Gender', '')}\n"
                f"annual income {row.get('Income', '')}\n"
                f"marital status {row.get('Marital_Status', '')}\n"
                f"education {row.get('Education', '')}\n"
                f"occupation {row.get('Occupation', '')}\n"
                f"policy type {random.choice(policy_types)}\n"
                f"claim amount {row.get('Claim_Amount', '')}\n"
                f"claim status {'approved' if random.random() > 0.3 else 'under review'}\n"
            ).lower().strip()

            out_file = dst / f"doc_{idx:04d}.txt"
            out_file.write_text(text, encoding="utf-8")
            idx += 1
            converted += 1
        except:
            continue

    return converted


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  NEXORA - Raw Data Converter")
    print("  Converting HTML / JPG / CSV into classification training data")
    print("=" * 70)

    results = {}

    # ── HTML CONVERSIONS ─────────────────────────────────────────────────
    print("\n[PHASE 1] Converting HTML files to text...")

    print("\n  [1/4] Balance Sheets (HTML -> balance_sheet)")
    n = convert_html_folder("Balance Sheets", "balance_sheet")
    results["balance_sheet (HTML)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [2/4] Income Statements (HTML -> profit_loss)")
    n = convert_html_folder("Income Statement", "profit_loss")
    results["profit_loss (HTML)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [3/4] Cash Flow (HTML -> cash_flow)")
    n = convert_html_folder("Cash Flow", "cash_flow")
    results["cash_flow (HTML)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [4/4] Notes/Others (HTML -> other)")
    # Don't add to 'other' since it already has 1016 files
    # n = convert_html_folder("Others", "other")
    print("  -> Skipped (other/ already has 1016 files)")
    results["other (HTML)"] = 0

    # ── JPG/IMAGE OCR CONVERSIONS ─────────────────────────────────────────
    print("\n[PHASE 2] Converting JPG images via OCR...")

    print("\n  [1/4] Bank Statements (JPG -> bank_statement)")
    n = convert_jpg_folder("Bank Statement", "bank_statement")
    results["bank_statement (JPG)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [2/4] Salary Slips (JPG -> salary_slip)")
    n = convert_jpg_folder("Salary Slip", "salary_slip")
    results["salary_slip (JPG)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [3/4] ITR / Form 16 (JPG -> tax_return)")
    n = convert_jpg_folder("ITR_Form 16", "tax_return")
    results["tax_return (JPG)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [4/4] Checks (JPG -> check)")
    n = convert_jpg_folder("Check", "check")
    results["check (JPG)"] = n
    print(f"  -> Converted: {n} files")

    # ── CSV CONVERSIONS ───────────────────────────────────────────────────
    print("\n[PHASE 3] Converting CSV data to text...")

    print("\n  [1/3] bankstatements.csv -> bank_statement")
    n = convert_bankstatements_csv()
    results["bank_statement (CSV)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [2/3] data_synthetic.csv -> insurance_policy")
    n = convert_insurance_csv()
    results["insurance_policy (CSV)"] = n
    print(f"  -> Converted: {n} files")

    print("\n  [3/3] insurance_dataset.csv -> insurance_policy")
    n = convert_insurance_claims_csv()
    results["insurance_claims (CSV)"] = n
    print(f"  -> Converted: {n} files")

    # ── SUMMARY ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  CONVERSION SUMMARY")
    print("=" * 70)

    total_new = 0
    for source, count in results.items():
        status = "[OK]" if count > 0 else "[--]"
        print(f"  {status} {source:<35} {count:>5} files")
        total_new += count

    print(f"\n  Total new files created: {total_new}")

    # Print full classification directory state
    print("\n" + "=" * 70)
    print("  FULL CLASSIFICATION DATA STATE")
    print("=" * 70)

    grand_total = 0
    for folder in sorted(CLASSIFICATION.iterdir()):
        if folder.is_dir():
            count = len(list(folder.glob("*.txt")))
            status = "[OK]" if count >= 100 else "[!!]"
            print(f"  {status} {folder.name:<25} {count:>6} files")
            grand_total += count

    print(f"  {'':25} {'=' * 12}")
    print(f"  {'GRAND TOTAL':<25} {grand_total:>6} files")
    print("=" * 70)


if __name__ == "__main__":
    main()
