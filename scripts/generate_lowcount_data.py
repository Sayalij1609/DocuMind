"""
================================================================================
NEXORA - Synthetic Data Generator for Low-Count Categories
================================================================================
Generates training data for: salary_slip, check, cash_flow, tax_return
These categories had insufficient real data after OCR/HTML conversion.
================================================================================
"""

import os
import random
import string
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLASSIFICATION_DIR = BASE_DIR / "data" / "classification"
NUM_SAMPLES = 400  # Per category

# ── Shared Data Pools ────────────────────────────────────────────────────────
INDIAN_NAMES = [
    "rajesh kumar", "priya sharma", "amit patel", "neha gupta", "suresh mehta",
    "anita singh", "vikram joshi", "deepika nair", "ramesh yadav", "pooja reddy",
    "arun kumar gupta", "meera devi", "sanjay verma", "kavita mishra", "rohit jain",
    "sunita agarwal", "manish tiwari", "rekha bose", "dinesh choudhary", "swati pandey",
    "manoj bhatt", "nisha kapoor", "ashok malhotra", "renu saxena", "vijay thakur",
    "geeta iyer", "prakash nambiar", "lalita menon", "harish shenoy", "usha pillai",
    "kiran desai", "nitin kulkarni", "asha patil", "tushar gaikwad", "smita jog",
    "gaurav bansal", "divya arora", "naveen sethi", "komal bajaj", "tarun dhawan",
]

COMPANIES = [
    "tata consultancy services", "infosys limited", "wipro technologies",
    "reliance industries", "hdfc bank limited", "icici bank",
    "larsen and toubro", "hindustan unilever", "bharti airtel",
    "tech mahindra", "hcl technologies", "adani enterprises",
    "sun pharma", "maruti suzuki india", "asian paints",
    "titan company", "nestle india", "ultratech cement",
    "godrej consumer products", "dabur india", "pidilite industries",
    "mahindra and mahindra", "hero motocorp", "bajaj auto",
    "cipla limited", "dr reddys laboratories", "divis laboratories",
    "kotak mahindra bank", "axis bank", "state bank of india",
]

BANKS = [
    "state bank of india", "hdfc bank", "icici bank", "axis bank",
    "punjab national bank", "bank of baroda", "canara bank",
    "kotak mahindra bank", "union bank of india", "idbi bank",
    "indian bank", "bank of india", "central bank of india",
    "yes bank", "indusind bank", "federal bank", "bandhan bank",
]

CITIES = [
    "mumbai", "delhi", "bangalore", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow",
    "kochi", "chandigarh", "indore", "bhopal", "nagpur",
]

DESIGNATIONS = [
    "software engineer", "senior developer", "project manager",
    "data analyst", "business analyst", "team lead",
    "assistant manager", "deputy manager", "general manager",
    "senior consultant", "associate director", "vice president",
    "chief technology officer", "accounts executive", "hr executive",
    "marketing manager", "product manager", "operations head",
    "sales executive", "quality analyst", "devops engineer",
]

DEPARTMENTS = [
    "information technology", "engineering", "finance",
    "human resources", "marketing", "operations",
    "sales", "research and development", "administration",
    "quality assurance", "product development", "accounts",
]


def rand_int(low, high):
    return random.randint(low, high)

def rand_date():
    y = random.randint(2019, 2025)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return random.choice([f"{d:02d}-{m:02d}-{y}", f"{d:02d}/{m:02d}/{y}", f"{y}-{m:02d}-{d:02d}"])

def rand_pan():
    return f"{''.join(random.choices(string.ascii_uppercase, k=5))}{rand_int(1000,9999)}{''.join(random.choices(string.ascii_uppercase, k=1))}"

def rand_account():
    return ''.join(random.choices(string.digits, k=random.randint(10, 14)))

def rand_ifsc():
    return f"{''.join(random.choices(string.ascii_uppercase, k=4))}0{rand_int(100000, 999999)}"

def ocr_noise(text, rate=0.03):
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < rate and chars[i].isalpha():
            n = random.choice(["swap", "drop", "double"])
            if n == "swap" and i + 1 < len(chars):
                chars[i], chars[i+1] = chars[i+1], chars[i]
            elif n == "drop":
                chars[i] = ""
            elif n == "double":
                chars[i] = chars[i] * 2
    return "".join(chars)

def next_doc_index(folder):
    existing = sorted(folder.glob("doc_*.txt"))
    if not existing:
        return 1
    try:
        return int(existing[-1].stem.split("_")[1]) + 1
    except:
        return len(existing) + 1


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 1: SALARY SLIP
# ═══════════════════════════════════════════════════════════════════════════════
def generate_salary_slip():
    name = random.choice(INDIAN_NAMES)
    company = random.choice(COMPANIES)
    emp_id = f"EMP{rand_int(1000, 99999)}"
    designation = random.choice(DESIGNATIONS)
    department = random.choice(DEPARTMENTS)
    pan = rand_pan()
    uan = f"{rand_int(100000000000, 999999999999)}"
    bank = random.choice(BANKS)
    account = rand_account()
    month = random.choice(["january","february","march","april","may","june",
                           "july","august","september","october","november","december"])
    year = rand_int(2020, 2025)
    city = random.choice(CITIES)

    basic = rand_int(15000, 120000)
    hra = round(basic * random.uniform(0.3, 0.5))
    da = round(basic * random.uniform(0.05, 0.15))
    special = rand_int(2000, 25000)
    conveyance = random.choice([1600, 3200, 4000, 5000])
    medical = random.choice([1250, 2500, 5000])
    lta = rand_int(0, 5000)
    bonus = random.choice([0, 0, 0, rand_int(2000, 15000)])

    gross = basic + hra + da + special + conveyance + medical + lta + bonus

    pf = round(basic * 0.12)
    esi = round(gross * 0.0075) if gross < 21000 else 0
    prof_tax = random.choice([0, 200, 200, 200, 2500])
    tds = round(gross * random.uniform(0.0, 0.15))

    total_deductions = pf + esi + prof_tax + tds
    net = gross - total_deductions

    templates = [
        # Template 1: Detailed payslip
        f"""salary slip payslip
company {company}
pay period {month} {year}
employee name {name}
employee id {emp_id}
designation {designation}
department {department}
date of joining {rand_date()}
pan number {pan}
uan {uan}
bank account {account} {bank}
location {city}

earnings
basic salary {basic}
house rent allowance hra {hra}
dearness allowance da {da}
special allowance {special}
conveyance allowance {conveyance}
medical allowance {medical}
leave travel allowance lta {lta}
performance bonus {bonus}
gross salary {gross}

deductions
provident fund pf {pf}
employee state insurance esi {esi}
professional tax {prof_tax}
income tax tds {tds}
total deductions {total_deductions}

net pay {net}
net salary payable in words {net} rupees only
total working days {random.choice([22, 23, 24, 25, 26])}
days present {random.choice([20, 21, 22, 23, 24, 25])}
leave taken {random.choice([0, 0, 1, 1, 2, 3])}""",

        # Template 2: Compact payslip
        f"""payslip for {month} {year}
{company} {city}
emp {emp_id} name {name}
designation {designation} dept {department}
pan {pan} uan {uan}

earnings                deductions
basic     {basic:<10}  pf        {pf}
hra       {hra:<10}  esi       {esi}
da        {da:<10}  prof tax  {prof_tax}
special   {special:<10}  tds       {tds}
conveyance {conveyance}
medical   {medical}
gross     {gross}    total ded {total_deductions}

net pay {net}
bank {bank} a/c {account}
pay date {rand_int(25,30)}-{month[:3]}-{year}""",

        # Template 3: CTC breakdown
        f"""monthly salary statement
{company}
employee {name} id {emp_id}
grade {random.choice(['l1','l2','l3','l4','l5','m1','m2','s1','s2'])}
cost centre {random.choice(['cc100','cc200','cc300','cc400','cc500'])}
month {month} {year}

fixed pay
basic {basic} hra {hra} da {da}
special allowance {special}
total fixed {basic + hra + da + special}

flexible benefits
conveyance {conveyance} medical {medical} lta {lta}
total flexible {conveyance + medical + lta}

variable pay
bonus {bonus}

total gross earnings {gross}
employer pf contribution {pf}
ctc cost to company {gross + pf}

deductions
employee pf {pf} prof tax {prof_tax} tds {tds}
total deductions {total_deductions}

take home pay net salary {net}""",

        # Template 4: Short format
        f"""salary slip {month} {year}
{company}
name {name} emp id {emp_id}
basic {basic} hra {hra} da {da} allowances {special + conveyance + medical}
gross {gross}
pf {pf} tax {tds} other {esi + prof_tax}
deductions {total_deductions}
net pay {net}
credited to {bank} a/c {account}""",
    ]

    text = random.choice(templates)
    if random.random() < 0.12:
        text = ocr_noise(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 2: CHECK / CHEQUE
# ═══════════════════════════════════════════════════════════════════════════════
def generate_check():
    payer = random.choice(INDIAN_NAMES)
    payee = random.choice(INDIAN_NAMES)
    while payee == payer:
        payee = random.choice(INDIAN_NAMES)

    bank = random.choice(BANKS)
    branch = f"{random.choice(CITIES)} {random.choice(['main branch','central branch','mg road branch','station road branch','sector branch','commercial branch'])}"
    amount = random.choice([500, 1000, 2500, 5000, 7500, 10000, 15000, 25000, 50000, 75000, 100000, 250000, 500000])
    ifsc = rand_ifsc()
    account = rand_account()
    cheque_no = f"{rand_int(100000, 999999)}"
    date = rand_date()
    micr = f"{rand_int(100000000, 999999999)}"

    def words(num):
        """Simple amount to words."""
        if num >= 100000:
            return f"{num // 100000} lakh {(num % 100000) // 1000} thousand" if num % 100000 else f"{num // 100000} lakh"
        elif num >= 1000:
            return f"{num // 1000} thousand {num % 1000}" if num % 1000 else f"{num // 1000} thousand"
        else:
            return str(num)

    templates = [
        # Template 1: Standard cheque
        f"""cheque check
{bank}
branch {branch}
ifsc code {ifsc}
date {date}
pay {payee}
or bearer
rupees {words(amount)} only
amount {amount}
account number {account}
cheque number {cheque_no}
micr code {micr}
signed {payer}""",

        # Template 2: Account payee cheque
        f"""account payee cheque
{bank} {branch}
ifsc {ifsc} micr {micr}
date {date}
pay to {payee}
amount in words {words(amount)} rupees only
amount in figures rs {amount}
a/c no {account}
cheque no {cheque_no}
drawn on {bank}
{random.choice(['account payee only', 'not negotiable', 'bearer'])}
authorized signatory {payer}""",

        # Template 3: Demand draft
        f"""demand draft dd
{bank} {branch}
dd number {rand_int(100000, 999999)}
date {date}
pay {payee}
sum of rupees {words(amount)} only
rs {amount}
payable at {random.choice(CITIES)}
application reference {rand_int(10000, 99999)}
purchaser {payer}
valid for 3 months from date of issue
ifsc {ifsc}""",

        # Template 4: OCR-style cheque read
        f"""cheque scan
bank {bank}
cheque no {cheque_no} date {date}
payee {payee}
amount {amount} rs
words {words(amount)} only
account {account}
ifsc {ifsc} micr {micr}
drawer {payer}
clearing status {random.choice(['cleared', 'presented', 'pending', 'returned'])}
{random.choice(['', 'reason ' + random.choice(['insufficient funds', 'signature mismatch', 'date expired', ''])])}""",

        # Template 5: Cancelled cheque
        f"""cancelled cheque
{bank}
branch {branch}
account holder {payer}
account number {account}
ifsc code {ifsc}
micr code {micr}
cheque number {cheque_no}
this cheque is cancelled
used for verification of bank account details
account type {random.choice(['savings', 'current', 'salary'])}""",
    ]

    text = random.choice(templates)
    if random.random() < 0.15:
        text = ocr_noise(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 3: CASH FLOW STATEMENT
# ═══════════════════════════════════════════════════════════════════════════════
def generate_cash_flow():
    company = random.choice(COMPANIES)
    year = rand_int(2019, 2025)
    unit = random.choice(["in lakhs", "in crores", "in thousands", "in millions"])

    net_profit = rand_int(50000, 5000000)
    depreciation = rand_int(5000, 500000)
    interest_paid = rand_int(2000, 200000)
    interest_received = rand_int(500, 50000)
    wc_changes = rand_int(-200000, 200000)
    tax_paid = rand_int(5000, 500000)
    op_cash = net_profit + depreciation + interest_paid - interest_received + wc_changes - tax_paid

    capex = rand_int(10000, 1000000)
    investments_purchased = rand_int(0, 500000)
    investments_sold = rand_int(0, 300000)
    inv_cash = -capex - investments_purchased + investments_sold

    borrowings = rand_int(0, 500000)
    repayments = rand_int(0, 400000)
    dividends = rand_int(0, 200000)
    equity = rand_int(0, 100000)
    fin_cash = borrowings - repayments - dividends + equity - interest_paid

    net_change = op_cash + inv_cash + fin_cash
    opening_cash = rand_int(10000, 500000)
    closing_cash = opening_cash + net_change

    receivables_change = rand_int(-100000, 100000)
    payables_change = rand_int(-80000, 80000)
    inventory_change = rand_int(-60000, 60000)

    templates = [
        # Template 1: Full statement
        f"""cash flow statement
{company}
for the year ended 31 march {year}
{unit}

a cash flow from operating activities
net profit before tax {net_profit}
adjustments for
depreciation and amortisation {depreciation}
interest expense {interest_paid}
interest income {-interest_received}
loss gain on sale of assets {rand_int(-5000, 5000)}
provision for doubtful debts {rand_int(0, 10000)}
operating profit before working capital changes {net_profit + depreciation}

changes in working capital
increase decrease in trade receivables {receivables_change}
increase decrease in inventories {inventory_change}
increase decrease in trade payables {payables_change}
increase decrease in other current assets {rand_int(-20000, 20000)}
cash generated from operations {op_cash + tax_paid}
income tax paid {-tax_paid}
net cash from operating activities {op_cash}

b cash flow from investing activities
purchase of property plant and equipment {-capex}
purchase of investments {-investments_purchased}
proceeds from sale of investments {investments_sold}
interest received {interest_received}
net cash used in investing activities {inv_cash}

c cash flow from financing activities
proceeds from borrowings {borrowings}
repayment of borrowings {-repayments}
dividends paid {-dividends}
proceeds from issue of equity shares {equity}
interest paid {-interest_paid}
net cash from financing activities {fin_cash}

net increase decrease in cash and cash equivalents {net_change}
cash and cash equivalents at beginning of year {opening_cash}
cash and cash equivalents at end of year {closing_cash}""",

        # Template 2: Condensed format
        f"""statement of cash flows
{company} fy {year-1}-{str(year)[2:]}
{unit}

operating activities
profit before tax {net_profit}
depreciation {depreciation}
working capital adjustments {wc_changes}
tax paid {-tax_paid}
net operating cash flow {op_cash}

investing activities
capital expenditure {-capex}
investment purchases {-investments_purchased}
investment proceeds {investments_sold}
net investing cash flow {inv_cash}

financing activities
borrowings net {borrowings - repayments}
dividend paid {-dividends}
share capital raised {equity}
net financing cash flow {fin_cash}

net change in cash {net_change}
opening balance {opening_cash}
closing cash balance {closing_cash}""",

        # Template 3: Quarterly cash flow
        f"""quarterly cash flow report
{company}
quarter q{rand_int(1,4)} fy {year-1}-{str(year)[2:]}
{unit}

cash from operations {op_cash}
cash from investing {inv_cash}
cash from financing {fin_cash}
free cash flow {op_cash - capex}
net cash movement {net_change}
cash position start {opening_cash}
cash position end {closing_cash}
capex {capex}
working capital change {wc_changes}
debt repayment {repayments}""",

        # Template 4: Short summary
        f"""cash flow summary {company}
year ended march {year} {unit}
operating {op_cash}
investing {inv_cash}
financing {fin_cash}
net change {net_change}
opening cash {opening_cash}
closing cash {closing_cash}
free cash flow {op_cash - capex}""",
    ]

    text = random.choice(templates)
    if random.random() < 0.10:
        text = ocr_noise(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 4: TAX RETURN (ITR / FORM 16)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_tax_return():
    name = random.choice(INDIAN_NAMES)
    pan = rand_pan()
    employer = random.choice(COMPANIES)
    tan = f"{''.join(random.choices(string.ascii_uppercase, k=4))}{rand_int(10000,99999)}{''.join(random.choices(string.ascii_uppercase, k=1))}"
    city = random.choice(CITIES)
    ay = rand_int(2021, 2026)
    fy = ay - 1

    gross_salary = rand_int(300000, 5000000)
    hra_exempt = round(gross_salary * random.uniform(0.1, 0.2))
    std_deduction = 50000
    net_salary = gross_salary - hra_exempt - std_deduction

    sec_80c = min(rand_int(10000, 200000), 150000)
    sec_80d = min(rand_int(0, 50000), 50000)
    sec_80g = rand_int(0, 20000)
    sec_80e = rand_int(0, 30000)
    nps_80ccd = rand_int(0, 50000)
    total_deductions = sec_80c + sec_80d + sec_80g + sec_80e + nps_80ccd

    taxable = max(net_salary - total_deductions, 0)

    # Simple Indian tax calc
    if taxable <= 250000:
        tax = 0
    elif taxable <= 500000:
        tax = round((taxable - 250000) * 0.05)
    elif taxable <= 1000000:
        tax = 12500 + round((taxable - 500000) * 0.20)
    else:
        tax = 112500 + round((taxable - 1000000) * 0.30)

    cess = round(tax * 0.04)
    total_tax = tax + cess
    tds_deducted = round(total_tax * random.uniform(0.85, 1.05))
    refund_due = max(tds_deducted - total_tax, 0)

    itr_form = random.choice(["itr-1 sahaj", "itr-2", "itr-3", "itr-4 sugam"])
    filing_date = f"{rand_int(1,31):02d}-{random.choice(['jul','aug','sep','oct','nov','dec'])}-{ay}"
    ack_no = f"{rand_int(100000000000000, 999999999999999)}"

    templates = [
        # Template 1: ITR filing
        f"""income tax return
assessment year {ay}-{str(ay+1)[2:]}
form {itr_form}
name {name}
pan {pan}
address {rand_int(1,500)} {random.choice(['mg road','nehru nagar','gandhi path','subhash marg'])} {city}
residential status resident
date of birth {rand_date()}
filing date {filing_date}
acknowledgement number {ack_no}

income details
income from salary {gross_salary}
less hra exemption {hra_exempt}
less standard deduction {std_deduction}
net salary income {net_salary}
income from house property {random.choice([0, 0, -rand_int(10000, 200000)])}
income from other sources {rand_int(0, 50000)}
gross total income {net_salary + rand_int(0, 50000)}

deductions under chapter via
section 80c life insurance pf ppf {sec_80c}
section 80d health insurance premium {sec_80d}
section 80g donations {sec_80g}
section 80e education loan interest {sec_80e}
section 80ccd nps contribution {nps_80ccd}
total deductions {total_deductions}

total taxable income {taxable}
tax on total income {tax}
health and education cess 4 percent {cess}
total tax liability {total_tax}
tds already deducted {tds_deducted}
advance tax paid {rand_int(0, 10000)}
self assessment tax {max(total_tax - tds_deducted, 0)}
refund due {refund_due}
verification i {name} do hereby declare that the information given is true""",

        # Template 2: Form 16
        f"""form 16
certificate under section 203 of the income tax act 1961
for tax deducted at source on salary
part a
name of employer {employer}
tan of employer {tan}
pan of employer {''.join(random.choices(string.ascii_uppercase, k=5))}{rand_int(1000,9999)}{''.join(random.choices(string.ascii_uppercase, k=1))}
name of employee {name}
pan of employee {pan}
assessment year {ay}-{str(ay+1)[2:]}
period from 01-04-{fy} to 31-03-{ay}
address of employer {city}

summary of tax deducted at source
quarter 1 apr jun {round(tds_deducted * 0.25)}
quarter 2 jul sep {round(tds_deducted * 0.25)}
quarter 3 oct dec {round(tds_deducted * 0.25)}
quarter 4 jan mar {round(tds_deducted * 0.25)}
total tds {tds_deducted}

part b
gross salary {gross_salary}
less allowances exempt hra {hra_exempt}
net salary {net_salary}
standard deduction us 16ia {std_deduction}
income chargeable under salaries {net_salary}
deductions under chapter via 80c {sec_80c} 80d {sec_80d}
total taxable income {taxable}
tax payable {total_tax}
tax deducted {tds_deducted}""",

        # Template 3: TDS certificate short
        f"""tds certificate form 16
employer {employer} tan {tan}
employee {name} pan {pan}
fy {fy}-{str(ay)[2:]} ay {ay}-{str(ay+1)[2:]}
gross salary {gross_salary}
exempt allowances {hra_exempt}
standard deduction {std_deduction}
chapter via deductions {total_deductions}
taxable income {taxable}
tax payable {total_tax}
tds deducted {tds_deducted}
{f'refund due {refund_due}' if refund_due > 0 else f'balance tax {max(total_tax - tds_deducted, 0)}'}""",

        # Template 4: 26AS tax credit
        f"""form 26as annual tax statement
name {name} pan {pan}
financial year {fy}-{str(ay)[2:]}

part a tds on salary
employer {employer} tan {tan}
total amount paid {gross_salary}
tds deducted {tds_deducted}
tds deposited {tds_deducted}

part a1 tds on other income
{random.choice(['bank interest tds ' + str(rand_int(1000, 10000)), 'no entries'])}

part b advance tax self assessment tax
challan {rand_int(10000, 99999)} bsr code {rand_int(1000000, 9999999)}
amount {max(total_tax - tds_deducted, 0)}

total tax credit available {tds_deducted + rand_int(0, 10000)}""",
    ]

    text = random.choice(templates)
    if random.random() < 0.12:
        text = ocr_noise(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
GENERATORS = {
    "salary_slip": generate_salary_slip,
    "check": generate_check,
    "cash_flow": generate_cash_flow,
    "tax_return": generate_tax_return,
}

def main():
    print("=" * 70)
    print("  NEXORA - Synthetic Generator for Low-Count Categories")
    print("=" * 70)

    total_generated = 0

    for category, generator in GENERATORS.items():
        output_dir = CLASSIFICATION_DIR / category
        output_dir.mkdir(parents=True, exist_ok=True)

        idx = next_doc_index(output_dir)
        existing = idx - 1

        print(f"\n[DIR] Category: {category}")
        print(f"      Existing files: {existing}")
        print(f"      Generating: {NUM_SAMPLES} new samples...")

        for i in range(NUM_SAMPLES):
            doc_num = idx + i
            filepath = output_dir / f"doc_{doc_num:04d}.txt"
            text = generator()
            filepath.write_text(text, encoding="utf-8")

        final_count = len(list(output_dir.glob("doc_*.txt")))
        print(f"      [OK] Done! Total files now: {final_count}")
        total_generated += NUM_SAMPLES

    print(f"\n{'=' * 70}")
    print(f"  COMPLETE: Generated {total_generated} files across {len(GENERATORS)} categories")
    print(f"{'=' * 70}")

    # Full summary
    print(f"\nFULL CLASSIFICATION DATA STATE:")
    print(f"{'=' * 50}")
    grand_total = 0
    for folder in sorted(CLASSIFICATION_DIR.iterdir()):
        if folder.is_dir():
            count = len(list(folder.glob("*.txt")))
            status = "[OK]" if count >= 100 else "[!!]"
            print(f"  {status} {folder.name:<25} {count:>6} files")
            grand_total += count
    print(f"  {'=' * 37}")
    print(f"  {'GRAND TOTAL':<25} {grand_total:>6} files")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
