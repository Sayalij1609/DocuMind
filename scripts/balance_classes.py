"""
================================================================================
NEXORA - Class Balancer
================================================================================
1. Generates synthetic data for under-represented categories
2. Caps over-represented categories by removing excess files
Target: ~500-600 files per category for balanced training
================================================================================
"""

import os
import random
import string
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLASSIFICATION_DIR = BASE_DIR / "data" / "classification"

# ── Target range ──────────────────────────────────────────────────────────────
TARGET_MIN = 450
TARGET_MAX = 650

# ── Shared data pools ─────────────────────────────────────────────────────────
INDIAN_NAMES = [
    "rajesh kumar", "priya sharma", "amit patel", "neha gupta", "suresh mehta",
    "anita singh", "vikram joshi", "deepika nair", "ramesh yadav", "pooja reddy",
    "arun kumar gupta", "meera devi", "sanjay verma", "kavita mishra", "rohit jain",
    "sunita agarwal", "manish tiwari", "rekha bose", "dinesh choudhary", "swati pandey",
    "manoj bhatt", "nisha kapoor", "ashok malhotra", "renu saxena", "vijay thakur",
    "geeta iyer", "prakash nambiar", "lalita menon", "harish shenoy", "usha pillai",
]

COMPANIES = [
    "tata consultancy services", "infosys limited", "wipro technologies",
    "reliance industries", "hdfc bank limited", "icici bank",
    "larsen and toubro", "hindustan unilever", "bharti airtel",
    "tech mahindra", "hcl technologies", "adani enterprises",
    "sun pharma", "maruti suzuki india", "asian paints",
    "titan company", "nestle india", "ultratech cement",
    "bajaj finserv", "kotak mahindra bank", "axis bank",
    "mahindra and mahindra", "hero motocorp", "cipla limited",
]

BANKS = [
    "state bank of india", "hdfc bank", "icici bank", "axis bank",
    "punjab national bank", "bank of baroda", "canara bank",
    "kotak mahindra bank", "union bank of india", "idbi bank",
    "yes bank", "indusind bank", "federal bank", "bandhan bank",
]

CITIES = [
    "mumbai", "delhi", "bangalore", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow",
]

def ri(a, b): return random.randint(a, b)
def rd(): return random.choice([f"{ri(1,28):02d}-{ri(1,12):02d}-{ri(2019,2025)}", f"{ri(2019,2025)}-{ri(1,12):02d}-{ri(1,28):02d}"])
def rpan(): return f"{''.join(random.choices(string.ascii_uppercase, k=5))}{ri(1000,9999)}{''.join(random.choices(string.ascii_uppercase, k=1))}"
def racct(): return ''.join(random.choices(string.digits, k=ri(10,14)))
def rifsc(): return f"{''.join(random.choices(string.ascii_uppercase, k=4))}0{ri(100000,999999)}"

def next_idx(folder):
    existing = sorted(folder.glob("doc_*.txt"))
    if not existing:
        return 1
    try:
        return int(existing[-1].stem.split("_")[1]) + 1
    except:
        return len(existing) + 1


# ═══════════════════════════════════════════════════════════════════════════════
# BANK STATEMENT GENERATOR (need ~400 more)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_bank_statement():
    name = random.choice(INDIAN_NAMES)
    bank = random.choice(BANKS)
    account = racct()
    ifsc = rifsc()
    city = random.choice(CITIES)
    acct_type = random.choice(["savings", "current", "salary"])
    month = random.choice(["january","february","march","april","may","june",
                           "july","august","september","october","november","december"])
    year = ri(2020, 2025)

    opening = ri(5000, 800000)
    balance = opening
    txns = []
    num_txns = ri(8, 25)

    modes = ["upi", "neft", "rtgs", "imps", "atm", "cheque", "pos", "auto debit", "ecs", "cash"]
    payees = ["amazon", "flipkart", "swiggy", "zomato", "electricity board", "mobile recharge",
              "rent payment", "grocery store", "petrol pump", "insurance premium",
              "mutual fund sip", "loan emi", "school fees", "medical store", "uber",
              random.choice(INDIAN_NAMES), random.choice(COMPANIES)]

    for _ in range(num_txns):
        is_credit = random.random() < 0.3
        amount = ri(100, 50000)
        mode = random.choice(modes)
        payee = random.choice(payees)
        day = ri(1, 28)

        if is_credit:
            balance += amount
            txns.append(f"{day:02d}-{month[:3]}-{year} credit {amount} balance {balance} {mode} {payee}")
        else:
            if balance > amount:
                balance -= amount
                txns.append(f"{day:02d}-{month[:3]}-{year} debit {amount} balance {balance} {mode} {payee}")

    templates = [
        # Template 1: Full statement
        f"""bank statement
{bank}
branch {city} {random.choice(['main branch','central branch','mg road'])}
account holder {name}
account number {account}
ifsc {ifsc}
account type {acct_type} account
statement period 01-{month[:3]}-{year} to 28-{month[:3]}-{year}
opening balance {opening}

date type amount balance mode description
{chr(10).join(txns)}

closing balance {balance}
total credits {sum(1 for t in txns if 'credit' in t)}
total debits {sum(1 for t in txns if 'debit' in t)}
total transactions {len(txns)}""",

        # Template 2: Passbook style
        f"""passbook statement {bank}
a/c {account} {acct_type} {name}
{city} branch ifsc {ifsc}
period {month} {year}
opening bal {opening}
{chr(10).join(txns)}
closing bal {balance}""",

        # Template 3: Digital statement
        f"""e statement {bank}
generated on {rd()}
customer {name} account {account}
type {acct_type} branch {city}
period {month} {year}
{chr(10).join(txns[:ri(5,10)])}
summary
opening {opening} closing {balance}
total inflow {ri(10000, 200000)} total outflow {ri(10000, 200000)}
average balance {ri(10000, 500000)}
minimum balance maintained {random.choice(['yes', 'no'])}""",
    ]

    return random.choice(templates).strip()


# ═══════════════════════════════════════════════════════════════════════════════
# BALANCE SHEET GENERATOR (need ~250 more)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_balance_sheet():
    company = random.choice(COMPANIES)
    year = ri(2019, 2025)
    unit = random.choice(["in lakhs", "in crores", "in thousands"])

    # Assets
    ppe = ri(100000, 5000000)
    intangible = ri(5000, 500000)
    investments_nc = ri(10000, 1000000)
    other_nc = ri(5000, 200000)
    total_nc_assets = ppe + intangible + investments_nc + other_nc

    inventory = ri(10000, 500000)
    receivables = ri(20000, 800000)
    cash = ri(5000, 300000)
    other_ca = ri(5000, 100000)
    investments_c = ri(0, 200000)
    total_ca = inventory + receivables + cash + other_ca + investments_c

    total_assets = total_nc_assets + total_ca

    # Equity & Liabilities
    share_capital = ri(10000, 500000)
    reserves = total_assets - share_capital - ri(100000, 1000000)
    total_equity = share_capital + max(reserves, 0)

    long_borrowings = ri(10000, 500000)
    provisions_nc = ri(5000, 100000)
    deferred_tax = ri(5000, 100000)
    total_ncl = long_borrowings + provisions_nc + deferred_tax

    total_cl = total_assets - total_equity - total_ncl
    short_borrowings = ri(5000, int(max(total_cl * 0.4, 10000)))
    trade_payables = ri(10000, int(max(total_cl * 0.3, 10000)))
    other_cl_val = max(total_cl - short_borrowings - trade_payables, 0)

    templates = [
        # Template 1: Full balance sheet
        f"""balance sheet
{company}
as at 31 march {year}
{unit}

i equity and liabilities
a shareholders funds
share capital {share_capital}
reserves and surplus {max(reserves, 0)}
total equity {total_equity}

b non current liabilities
long term borrowings {long_borrowings}
deferred tax liabilities net {deferred_tax}
long term provisions {provisions_nc}
total non current liabilities {total_ncl}

c current liabilities
short term borrowings {short_borrowings}
trade payables {trade_payables}
other current liabilities {other_cl_val}
total current liabilities {total_cl}

total equity and liabilities {total_assets}

ii assets
a non current assets
property plant and equipment {ppe}
intangible assets {intangible}
non current investments {investments_nc}
other non current assets {other_nc}
total non current assets {total_nc_assets}

b current assets
inventories {inventory}
trade receivables {receivables}
cash and cash equivalents {cash}
short term investments {investments_c}
other current assets {other_ca}
total current assets {total_ca}

total assets {total_assets}""",

        # Template 2: Comparative
        f"""consolidated balance sheet {company}
as at march 31 {year} {unit}
particulars {year} {year-1}
assets
non current assets
fixed assets {ppe} {ri(100000,5000000)}
intangible assets {intangible} {ri(5000,500000)}
investments {investments_nc} {ri(10000,1000000)}
current assets
inventories {inventory} {ri(10000,500000)}
trade receivables {receivables} {ri(20000,800000)}
cash bank balances {cash} {ri(5000,300000)}
total assets {total_assets} {ri(200000,8000000)}
equity and liabilities
share capital {share_capital} {share_capital}
reserves {max(reserves, 0)} {ri(50000,3000000)}
borrowings {long_borrowings + short_borrowings} {ri(20000,800000)}
trade payables {trade_payables} {ri(10000,600000)}
total equity and liabilities {total_assets} {ri(200000,8000000)}""",

        # Template 3: Short format
        f"""balance sheet {company} march {year} {unit}
total assets {total_assets}
non current assets {total_nc_assets}
current assets {total_ca}
shareholders equity {total_equity}
non current liabilities {total_ncl}
current liabilities {total_cl}
net worth {total_equity}
debt equity ratio {round(long_borrowings / max(total_equity, 1), 2)}
current ratio {round(total_ca / max(total_cl, 1), 2)}
working capital {total_ca - total_cl}""",
    ]

    return random.choice(templates).strip()


# ═══════════════════════════════════════════════════════════════════════════════
# PROFIT & LOSS GENERATOR (need ~200 more)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_profit_loss():
    company = random.choice(COMPANIES)
    year = ri(2019, 2025)
    unit = random.choice(["in lakhs", "in crores", "in thousands"])

    revenue = ri(500000, 50000000)
    other_income = ri(5000, 500000)
    total_income = revenue + other_income

    cogs = round(revenue * random.uniform(0.4, 0.7))
    employee = round(revenue * random.uniform(0.08, 0.25))
    depreciation = ri(10000, 500000)
    finance_cost = ri(5000, 200000)
    other_expense = round(revenue * random.uniform(0.05, 0.15))
    total_expense = cogs + employee + depreciation + finance_cost + other_expense

    pbt = total_income - total_expense
    tax = round(max(pbt, 0) * random.uniform(0.20, 0.30))
    pat = pbt - tax
    oci = ri(-50000, 50000)
    total_ci = pat + oci
    eps = round(pat / ri(10000, 500000), 2)

    templates = [
        # Template 1: Full P&L
        f"""statement of profit and loss
{company}
for the year ended 31 march {year}
{unit}

income
revenue from operations {revenue}
other income {other_income}
total income {total_income}

expenses
cost of materials consumed {cogs}
employee benefits expense {employee}
depreciation and amortisation {depreciation}
finance costs {finance_cost}
other expenses {other_expense}
total expenses {total_expense}

profit before tax {pbt}
tax expense current tax {round(tax * 0.8)} deferred tax {round(tax * 0.2)}
total tax expense {tax}

profit for the year {pat}
other comprehensive income {oci}
total comprehensive income {total_ci}

earnings per share basic {eps} diluted {round(eps * 0.95, 2)}""",

        # Template 2: Income statement format
        f"""income statement {company}
fy {year-1}-{str(year)[2:]} {unit}
net sales revenue {revenue}
cost of goods sold {cogs}
gross profit {revenue - cogs}
gross margin {round((revenue - cogs) / revenue * 100, 1)} percent
operating expenses
salaries wages {employee}
depreciation {depreciation}
other operating expenses {other_expense}
total operating expenses {employee + depreciation + other_expense}
operating profit ebit {revenue - cogs - employee - depreciation - other_expense}
interest expense {finance_cost}
other income {other_income}
profit before tax {pbt}
income tax {tax}
net profit after tax {pat}
net profit margin {round(pat / revenue * 100, 1)} percent
ebitda {pbt + depreciation + finance_cost}""",

        # Template 3: Summary format
        f"""profit and loss account {company}
year ended march {year} {unit}
revenue {revenue} other income {other_income}
total income {total_income}
material cost {cogs} employee cost {employee}
depreciation {depreciation} interest {finance_cost}
other expenses {other_expense}
total expenses {total_expense}
pbt {pbt} tax {tax} pat {pat}
eps {eps}""",
    ]

    return random.choice(templates).strip()


# ═══════════════════════════════════════════════════════════════════════════════
# CAP OVER-REPRESENTED CLASSES
# ═══════════════════════════════════════════════════════════════════════════════
def cap_category(category: str, max_files: int):
    """Remove excess files from an over-represented category."""
    folder = CLASSIFICATION_DIR / category
    if not folder.exists():
        return 0

    all_files = sorted(folder.glob("doc_*.txt"))
    current_count = len(all_files)

    if current_count <= max_files:
        return 0

    # Remove the newest files (higher doc numbers = generated later = lower quality)
    files_to_remove = all_files[max_files:]
    removed = 0
    for f in files_to_remove:
        f.unlink()
        removed += 1

    return removed


# ═══════════════════════════════════════════════════════════════════════════════
# BOOST UNDER-REPRESENTED CLASSES
# ═══════════════════════════════════════════════════════════════════════════════
def boost_category(category: str, generator, target: int):
    """Generate synthetic samples to reach target count."""
    folder = CLASSIFICATION_DIR / category
    folder.mkdir(parents=True, exist_ok=True)

    current = len(list(folder.glob("doc_*.txt")))
    needed = target - current
    if needed <= 0:
        return 0

    idx = next_idx(folder)
    for i in range(needed):
        text = generator()
        filepath = folder / f"doc_{idx + i:04d}.txt"
        filepath.write_text(text, encoding="utf-8")

    return needed


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 70)
    print("  NEXORA - Class Balancer")
    print("  Balancing all categories to ~500-600 files each")
    print("=" * 70)

    # Show BEFORE state
    print("\nBEFORE:")
    for folder in sorted(CLASSIFICATION_DIR.iterdir()):
        if folder.is_dir():
            count = len(list(folder.glob("*.txt")))
            bar = "#" * (count // 50)
            print(f"  {folder.name:<25} {count:>6}  {bar}")

    # ── STEP 1: Cap over-represented categories ──────────────────────────
    print("\n[STEP 1] Capping over-represented categories...")

    caps = {
        "insurance_policy": 600,
        "other": 600,
        "invoice": 600,
        "purchase_order": 600,
    }

    for cat, max_count in caps.items():
        removed = cap_category(cat, max_count)
        if removed > 0:
            print(f"  Removed {removed} excess files from {cat}")
        else:
            print(f"  {cat}: already within limits")

    # ── STEP 2: Boost under-represented categories ───────────────────────
    print("\n[STEP 2] Boosting under-represented categories...")

    boosts = {
        "bank_statement": (generate_bank_statement, 500),
        "balance_sheet": (generate_balance_sheet, 500),
        "profit_loss": (generate_profit_loss, 500),
    }

    for cat, (gen, target) in boosts.items():
        added = boost_category(cat, gen, target)
        if added > 0:
            print(f"  Added {added} synthetic files to {cat}")
        else:
            print(f"  {cat}: already sufficient")

    # ── Show AFTER state ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("AFTER (BALANCED):")
    print("=" * 70)
    grand_total = 0
    for folder in sorted(CLASSIFICATION_DIR.iterdir()):
        if folder.is_dir():
            count = len(list(folder.glob("*.txt")))
            bar = "#" * (count // 50)
            status = "[OK]" if TARGET_MIN <= count <= TARGET_MAX else "[!!]"
            print(f"  {status} {folder.name:<25} {count:>6}  {bar}")
            grand_total += count

    print(f"  {'=' * 40}")
    print(f"  {'GRAND TOTAL':<25} {grand_total:>6} files")
    print(f"{'=' * 70}")
    print(f"\n  All categories are now balanced for optimal training!")


if __name__ == "__main__":
    main()
