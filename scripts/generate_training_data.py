"""
================================================================================
NEXORA — SYNTHETIC DATA GENERATOR + DATA STRUCTURING PIPELINE
================================================================================
Purpose  : 1. Generate synthetic training data for 3 missing categories
              (Insurance Policy, Loan Agreement, Audit Report)
           2. Convert existing raw data (HTML, JPG, CSV) into structured
              .txt files for the classification model
              
Usage    : python generate_training_data.py
Output   : data/classification/<category>/doc_XXXX.txt
================================================================================
"""

import os
import random
import string
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # Nexora root
CLASSIFICATION_DIR = BASE_DIR / "data" / "classification"
NUM_SAMPLES = 500  # Per category

# ─────────────────────────────────────────────────────────────────────────────
# SHARED DATA POOLS — realistic randomized values
# ─────────────────────────────────────────────────────────────────────────────
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
    "state bank of india", "axis bank", "kotak mahindra bank",
    "bajaj finserv", "larsen and toubro", "hindustan unilever",
    "bharti airtel", "tech mahindra", "hcl technologies",
    "adani enterprises", "sun pharma", "dr reddys laboratories",
    "maruti suzuki india", "asian paints", "titan company",
    "power grid corporation", "nestle india", "ultratech cement",
    "divi laboratories", "godrej consumer products", "dabur india",
    "pidilite industries", "mahindra and mahindra", "hero motocorp",
]

INSURANCE_COMPANIES = [
    "life insurance corporation of india", "sbi life insurance",
    "hdfc life insurance", "icici prudential life insurance",
    "max life insurance", "bajaj allianz life insurance",
    "tata aia life insurance", "kotak life insurance",
    "birla sun life insurance", "lic of india",
    "star health insurance", "new india assurance",
    "national insurance company", "united india insurance",
    "oriental insurance company", "iffco tokio general insurance",
    "bharti axa general insurance", "royal sundaram insurance",
    "reliance general insurance", "future generali insurance",
]

INSURANCE_PRODUCTS = [
    "jeevan amar term plan", "jeevan labh endowment plan",
    "smart protect term plan", "click 2 protect super plan",
    "saral jeevan bima plan", "ismart term plan",
    "eterm protection plan", "sampoorn suraksha kawach plan",
    "family health optima plan", "comprehensive health shield plan",
    "motor vehicle comprehensive plan", "home secure insurance plan",
    "travel guard insurance plan", "crop insurance pradhan mantri plan",
    "group term life plan", "personal accident cover plan",
    "critical illness benefit plan", "cancer protect plan",
    "retirement pension plan", "child education savings plan",
]

BANKS = [
    "state bank of india", "hdfc bank", "icici bank", "axis bank",
    "punjab national bank", "bank of baroda", "canara bank",
    "kotak mahindra bank", "union bank of india", "idbi bank",
    "indian bank", "bank of india", "central bank of india",
    "yes bank", "indusind bank", "federal bank",
]

AUDITOR_FIRMS = [
    "deloitte haskins and sells llp", "ernst and young llp",
    "kpmg india llp", "pricewaterhousecoopers llp",
    "bsr and co llp", "sr batliboi and co llp",
    "walker chandiok and co llp", "mska and associates",
    "sharp and tannan", "s r batliboi and associates llp",
    "ford rhodes parks and co llp", "lodha and co",
    "singhi and co", "price waterhouse and co llp",
    "grant thornton bharat llp", "bdo india llp",
]

CITIES = [
    "mumbai", "delhi", "bangalore", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow",
    "kochi", "chandigarh", "indore", "bhopal", "nagpur",
    "visakhapatnam", "coimbatore", "thiruvananthapuram", "gurgaon", "noida",
]

STATES = [
    "maharashtra", "delhi", "karnataka", "telangana", "tamil nadu",
    "west bengal", "rajasthan", "gujarat", "uttar pradesh", "kerala",
    "madhya pradesh", "punjab", "andhra pradesh", "haryana", "odisha",
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def rand_amount(low, high):
    return round(random.uniform(low, high), 2)

def rand_int(low, high):
    return random.randint(low, high)

def rand_date():
    y = random.randint(2019, 2025)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    fmt = random.choice([
        f"{d:02d}-{m:02d}-{y}",
        f"{d:02d}/{m:02d}/{y}",
        f"{y}-{m:02d}-{d:02d}",
    ])
    return fmt

def rand_pan():
    letters = ''.join(random.choices(string.ascii_uppercase, k=5))
    digits = ''.join(random.choices(string.digits, k=4))
    last = random.choice(string.ascii_uppercase)
    return f"{letters}{digits}{last}"

def rand_account():
    return ''.join(random.choices(string.digits, k=random.randint(10, 14)))

def rand_ifsc():
    bank_code = ''.join(random.choices(string.ascii_uppercase, k=4))
    branch = ''.join(random.choices(string.digits, k=7))
    return f"{bank_code}0{branch}"

def rand_policy_num(prefix="POL"):
    return f"{prefix}-{random.randint(2020,2025)}-{random.randint(100000,999999)}"

def rand_cin():
    return f"L{rand_int(10000,99999)}{''.join(random.choices(string.ascii_uppercase,k=2))}{rand_int(1990,2020)}PLC{rand_int(100000,999999)}"

def rand_membership():
    return f"0{rand_int(10000,99999)}"

def ocr_noise(text, noise_rate=0.03):
    """Add OCR-like noise to simulate Tesseract output"""
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < noise_rate and chars[i].isalpha():
            noise_type = random.choice(["swap", "drop", "double"])
            if noise_type == "swap" and i + 1 < len(chars):
                chars[i], chars[i+1] = chars[i+1], chars[i]
            elif noise_type == "drop":
                chars[i] = ""
            elif noise_type == "double":
                chars[i] = chars[i] * 2
    return "".join(chars)


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 1: INSURANCE POLICY GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def generate_insurance_policy():
    insurer = random.choice(INSURANCE_COMPANIES)
    product = random.choice(INSURANCE_PRODUCTS)
    holder = random.choice(INDIAN_NAMES)
    nominee = random.choice(INDIAN_NAMES)
    while nominee == holder:
        nominee = random.choice(INDIAN_NAMES)

    policy_num = rand_policy_num(random.choice(["LIC", "SBI", "HDFC", "ICICI", "MAX", "BAJAJ", "TATA"]))
    age = rand_int(21, 65)
    sum_assured = random.choice([500000, 1000000, 2500000, 5000000, 7500000, 10000000, 15000000, 20000000])
    premium = rand_int(2000, 85000)
    term = random.choice([10, 15, 20, 25, 30])
    start_date = rand_date()
    city = random.choice(CITIES)
    state = random.choice(STATES)
    pan = rand_pan()
    relationship = random.choice(["spouse", "son", "daughter", "mother", "father", "brother", "sister"])
    frequency = random.choice(["monthly", "quarterly", "half yearly", "yearly"])
    smoker = random.choice(["smoker", "non smoker"])
    payment = random.choice(["nach mandate", "ecs", "online payment", "cheque", "upi autopay"])
    bank = random.choice(BANKS)
    
    ins_type = random.choice(["life", "health", "motor", "property", "travel", "term"])
    
    templates = [
        # Template 1: Full policy schedule
        f"""insurance policy schedule
policy number {policy_num}
insurer {insurer}
product name {product}
policyholder name {holder}
date of birth {rand_date()} age {age} years
address {rand_int(1,500)} {random.choice(['mg road','nehru place','link road','ring road','main street'])} {city} {state} {rand_int(100000,999999)}
pan {pan}
sum assured {sum_assured}
policy type {ins_type} insurance
policy term {term} years premium paying term {term} years
{frequency} premium {premium}
risk commencement date {start_date}
maturity date {rand_date()}
nominee name {nominee} relationship {relationship}
nomination percentage 100
smoker status {smoker}
mode of premium payment {payment} {bank}
exclusions suicide within first year pre existing diseases for first {random.choice([2,3,4])} years""",

        # Template 2: Health insurance
        f"""health insurance policy certificate
insurer {insurer}
policy number {policy_num}
type of policy {random.choice(['individual', 'family floater', 'group'])} health insurance
insured name {holder} age {age}
sum insured {sum_assured}
annual premium {premium} inclusive of gst
policy period {start_date} to {rand_date()}
hospital room category {random.choice(['single private ac', 'twin sharing', 'general ward', 'any room'])}
co payment {random.choice([0, 10, 20])} percent
deductible {random.choice([0, 5000, 10000, 25000])}
waiting period 30 days initial {random.choice([2,3,4])} years pre existing
covered members {holder} {nominee}
network hospitals {rand_int(5000,15000)} hospitals across india
cashless facility available
sub limits room rent {random.choice(['1 percent', '2 percent', 'no sub limit'])} of sum insured
claim settlement ratio {random.choice(['95', '96', '97', '98'])} percent
tpa {random.choice(['medi assist', 'paramount health', 'md india', 'heritage health'])}""",

        # Template 3: Motor insurance
        f"""motor insurance policy
insurer {insurer}
policy number {rand_policy_num("MOT")}
insured name {holder}
vehicle registration number {random.choice(['MH','DL','KA','TN','AP','RJ','GJ'])}{rand_int(1,99):02d}{random.choice(['A','B','C','AB','CD'])}{rand_int(1000,9999)}
vehicle make {random.choice(['maruti suzuki','hyundai','tata motors','mahindra','honda','toyota','kia'])}
vehicle model {random.choice(['swift','creta','nexon','xuv700','city','fortuner','seltos'])}
year of manufacture {rand_int(2018,2025)}
engine number {rand_int(100000,999999)}
chassis number {''.join(random.choices(string.ascii_uppercase + string.digits, k=17))}
idv insured declared value {rand_int(200000,2500000)}
policy type {random.choice(['comprehensive','third party only','standalone own damage'])}
premium {premium} plus gst
ncb no claim bonus {random.choice([0, 20, 25, 35, 45, 50])} percent
addon covers {random.choice(['zero depreciation','engine protect','roadside assistance','return to invoice'])}
policy period {start_date} to {rand_date()}""",

        # Template 4: Short policy summary
        f"""insurance policy
policy no {policy_num} insurer {insurer}
plan {product} type {ins_type}
name {holder} age {age} pan {pan}
sum assured {sum_assured} premium {premium} {frequency}
term {term} years start {start_date}
nominee {nominee} {relationship}
status {smoker} payment {payment}""",
    ]
    
    text = random.choice(templates)
    if random.random() < 0.15:
        text = ocr_noise(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 2: LOAN AGREEMENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def generate_loan_agreement():
    borrower = random.choice(INDIAN_NAMES)
    co_borrower = random.choice(INDIAN_NAMES)
    while co_borrower == borrower:
        co_borrower = random.choice(INDIAN_NAMES)
    
    lender = random.choice(BANKS)
    loan_type = random.choice(["home loan", "personal loan", "car loan", "education loan",
                                "business loan", "gold loan", "loan against property",
                                "two wheeler loan", "consumer durable loan"])
    
    if loan_type == "home loan":
        amount = random.choice([2500000, 3500000, 5000000, 7500000, 10000000, 15000000])
        rate = round(random.uniform(7.5, 10.5), 2)
        tenure = random.choice([120, 180, 240, 300, 360])
    elif loan_type == "personal loan":
        amount = random.choice([100000, 200000, 300000, 500000, 1000000])
        rate = round(random.uniform(10.5, 18.0), 2)
        tenure = random.choice([12, 24, 36, 48, 60])
    elif loan_type == "car loan":
        amount = random.choice([300000, 500000, 800000, 1200000, 1500000])
        rate = round(random.uniform(7.0, 12.0), 2)
        tenure = random.choice([36, 48, 60, 72, 84])
    elif loan_type == "education loan":
        amount = random.choice([500000, 1000000, 1500000, 2000000, 3000000])
        rate = round(random.uniform(8.0, 12.0), 2)
        tenure = random.choice([60, 84, 120, 180])
    else:
        amount = random.choice([200000, 500000, 1000000, 2000000, 5000000])
        rate = round(random.uniform(9.0, 16.0), 2)
        tenure = random.choice([12, 24, 36, 48, 60, 84, 120])
    
    emi = round(amount * (rate/1200) * ((1 + rate/1200)**tenure) / (((1 + rate/1200)**tenure) - 1))
    total_interest = emi * tenure - amount
    processing_fee = round(amount * random.uniform(0.005, 0.03))
    disbursement_date = rand_date()
    loan_account = f"{''.join(random.choices(string.ascii_uppercase, k=2))}-{rand_int(2020,2025)}-{''.join(random.choices(string.ascii_uppercase, k=3))}-{rand_int(100000,999999)}"
    pan = rand_pan()
    rate_type = random.choice(["floating", "fixed"])
    city = random.choice(CITIES)
    
    templates = [
        # Template 1: Full sanction letter
        f"""loan sanction letter
loan account number {loan_account}
lender {lender}
borrower name {borrower} co borrower {co_borrower}
pan {pan}
address {rand_int(1,999)} {random.choice(['sector','block','lane','cross'])} {rand_int(1,50)} {city} {random.choice(STATES)} {rand_int(100000,999999)}
loan type {loan_type}
sanctioned amount {amount}
interest rate {rate} percent per annum {rate_type}
loan tenure {tenure} months {tenure // 12} years
emi amount {emi} per month
disbursement date {disbursement_date}
first emi date {rand_date()}
processing fee {processing_fee} plus gst
prepayment charges {'nil for floating rate' if rate_type == 'floating' else f'{random.choice([2,3,4])} percent of outstanding'}
total interest payable {round(total_interest)}
total repayment amount {round(amount + total_interest)}
repayment mode {random.choice(['nach','ecs','standing instruction','post dated cheques'])}
account for debit {rand_account()} {random.choice(BANKS)}""",

        # Template 2: EMI schedule / amortization
        f"""loan emi amortization schedule
loan account {loan_account} lender {lender}
borrower {borrower} loan type {loan_type}
principal amount {amount} rate of interest {rate} percent {rate_type}
tenure {tenure} months emi {emi}
month opening balance principal interest closing balance
1 {amount} {round(emi - amount*rate/1200)} {round(amount*rate/1200)} {round(amount - (emi - amount*rate/1200))}
2 {round(amount - (emi - amount*rate/1200))} {round(emi - (amount - (emi - amount*rate/1200))*rate/1200)} {round((amount - (emi - amount*rate/1200))*rate/1200)} {round(amount - 2*(emi - amount*rate/1200))}
3 {round(amount - 2*(emi - amount*rate/1200))} {round(emi - (amount - 2*(emi - amount*rate/1200))*rate/1200)} {round((amount - 2*(emi - amount*rate/1200))*rate/1200)} {round(amount - 3*(emi - amount*rate/1200))}
total emi payable {emi * tenure} total interest {round(total_interest)} total principal {amount}
processing fee {processing_fee} documentation charges {rand_int(500,5000)}
foreclosure charges {'nil' if rate_type == 'floating' else f'{random.choice([2,3])} percent'}""",

        # Template 3: Agreement format
        f"""loan agreement
this loan agreement is executed on {disbursement_date}
between {lender} hereinafter referred to as the lender
and {borrower} hereinafter referred to as the borrower
co applicant {co_borrower}
loan details
loan type {loan_type} loan amount {amount}
rate of interest {rate} percent per annum {rate_type}
{'linked to rplr rplr minus ' + str(round(random.uniform(0.1, 0.5), 2)) + ' percent' if rate_type == 'floating' else ''}
emi {emi} tenure {tenure} months
{'collateral property mortgage first charge' if loan_type in ['home loan', 'loan against property'] else 'unsecured loan'}
{'property address flat ' + str(rand_int(100,999)) + ' ' + random.choice(['sunrise towers','green valley','palm springs','royal residency']) + ' ' + city if loan_type == 'home loan' else ''}
the borrower agrees to repay the loan amount along with interest in equated monthly installments
default clause failure to pay emi for {random.choice([2,3])} consecutive months will result in loan recall
jurisdiction {city} courts
signatures borrower {borrower} lender authorized signatory""",

        # Template 4: Short format
        f"""loan sanction {loan_type}
a/c {loan_account} bank {lender}
borrower {borrower} pan {pan}
amount {amount} rate {rate} pct {rate_type}
tenure {tenure} months emi {emi}
disbursed {disbursement_date}
processing fee {processing_fee}
total payable {round(amount + total_interest)}""",
    ]
    
    text = random.choice(templates)
    if random.random() < 0.15:
        text = ocr_noise(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY 3: AUDIT REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════
def generate_audit_report():
    auditor_firm = random.choice(AUDITOR_FIRMS)
    company = random.choice(COMPANIES)
    partner = random.choice(INDIAN_NAMES)
    city = random.choice(CITIES)
    year = rand_int(2020, 2025)
    cin = rand_cin()
    membership = rand_membership()
    firm_reg = f"{rand_int(100000,999999)}W/W-{rand_int(100000,999999)}"
    
    opinion_type = random.choice(["unqualified", "qualified", "adverse", "disclaimer of opinion"])
    
    if opinion_type == "unqualified":
        opinion_text = "in our opinion and to the best of our information and according to the explanations given to us the aforesaid financial statements give a true and fair view in conformity with the accounting principles generally accepted in india"
    elif opinion_type == "qualified":
        opinion_text = f"except for the effects of the matter described in the basis for qualified opinion section the financial statements give a true and fair view of the financial position of {company}"
    elif opinion_type == "adverse":
        opinion_text = f"in our opinion because of the significance of the matter discussed in the basis for adverse opinion section the financial statements do not give a true and fair view of the state of affairs of {company}"
    else:
        opinion_text = f"because of the significance of the matter described in the basis for disclaimer of opinion section we were unable to obtain sufficient appropriate audit evidence to provide a basis for an opinion on the financial statements of {company}"
    
    kam_items = random.sample([
        "revenue recognition from long term contracts",
        "goodwill impairment assessment",
        "provision for expected credit losses",
        "valuation of investment property",
        "assessment of deferred tax assets",
        "litigation and contingent liabilities",
        "going concern assessment",
        "related party transactions",
        "inventory valuation and obsolescence",
        "impairment of trade receivables",
        "fair value of financial instruments",
        "recognition of government grants",
    ], k=random.randint(2, 4))
    
    caro_items = random.sample([
        "the company has maintained proper records showing full particulars of fixed assets",
        "physical verification of inventory has been conducted at reasonable intervals",
        "the company has not granted any loans to parties covered in the register",
        "the company has complied with provisions of section 185 and 186 of the companies act",
        "the company has not accepted deposits from the public",
        "the central government has prescribed maintenance of cost records under section 148",
        "the company is regular in depositing statutory dues with appropriate authorities",
        "the company has not defaulted in repayment of loans or borrowings",
        "the company has not raised money by way of initial public offer or further public offer",
        "no fraud by the company or on the company has been noticed or reported",
    ], k=random.randint(3, 5))
    
    templates = [
        # Template 1: Full statutory audit report
        f"""independent auditors report
to the members of {company}
cin {cin}
report on the audit of financial statements
opinion
we have audited the accompanying financial statements of {company} the company which comprise the balance sheet as at 31 march {year} the statement of profit and loss including other comprehensive income the statement of changes in equity and the cash flow statement for the year then ended and notes to the financial statements
{opinion_text}
basis for opinion
we conducted our audit in accordance with the standards on auditing sa specified under section 143 10 of the companies act 2013 our responsibilities under those standards are further described in the auditors responsibilities section
we are independent of the company in accordance with the code of ethics issued by the institute of chartered accountants of india icai
key audit matters
{chr(10).join(kam_items)}
information other than the financial statements and auditors report thereon
the companys management and board of directors are responsible for the other information
management responsibility for the financial statements
the companys management and board of directors are responsible for the preparation and presentation of these financial statements
report on other legal and regulatory requirements
as required by the companies auditors report order 2020 caro issued by the central government
{chr(10).join(caro_items)}
for {auditor_firm}
chartered accountants
firm registration number {firm_reg}
partner {partner}
membership number {membership}
udin {year}{membership}{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}
place {city} date {rand_int(15,30)}-{random.choice(['apr','may','jun'])}-{year}""",

        # Template 2: Internal audit report
        f"""internal audit report
company {company}
audit period q{rand_int(1,4)} fy {year-1}-{str(year)[2:]}
auditor {auditor_firm}
scope of audit
we have conducted an internal audit of the financial and operational controls of {company} for the period ended {rand_date()}
areas covered
financial controls and accounting processes
compliance with statutory and regulatory requirements
internal control over financial reporting
risk management framework assessment
key findings
observation 1 {random.choice(['accounts receivable aging beyond 90 days requires review', 'inventory count discrepancies noted in warehouse b', 'employee expense reimbursement process lacks adequate controls'])}
risk rating {random.choice(['high', 'medium', 'low'])}
recommendation strengthen reconciliation process and implement monthly reviews
observation 2 {random.choice(['vendor onboarding process does not include background verification', 'it access controls need strengthening for critical systems', 'revenue recognition policy requires update for new contracts'])}
risk rating {random.choice(['high', 'medium', 'low'])}
recommendation implement automated controls and periodic review mechanism
overall assessment
the internal controls are {random.choice(['adequate with scope for improvement', 'satisfactory with minor observations', 'needs significant strengthening'])}
prepared by {partner} {auditor_firm}
date {rand_date()}""",

        # Template 3: Tax audit report
        f"""tax audit report under section 44ab of the income tax act 1961
form no 3ca 3cd
name of the assessee {company}
pan {''.join(random.choices(string.ascii_uppercase, k=5))}{rand_int(1000,9999)}{''.join(random.choices(string.ascii_uppercase, k=1))}
address registered office {city} {random.choice(STATES)}
assessment year {year}-{str(year+1)[2:]}
previous year {year-1}-{str(year)[2:]}
nature of business {random.choice(['manufacturing', 'it services', 'trading', 'consulting', 'financial services'])}
total turnover gross receipts {rand_int(10000000, 500000000)}
net profit as per profit and loss account {rand_int(1000000, 50000000)}
additions disallowances
depreciation as per books {rand_int(100000, 5000000)}
depreciation as per income tax act {rand_int(100000, 5000000)}
disallowance under section 40a3 {rand_int(0, 100000)}
disallowance under section 43b {rand_int(0, 200000)}
adjusted net profit {rand_int(1000000, 50000000)}
tax payable {rand_int(500000, 15000000)}
tds deducted and deposited {random.choice(['yes all tds deducted deposited within due dates', 'delay in deposit of tds for months of march and september'])}
gst compliance {random.choice(['regular filing with no defaults', 'input tax credit reconciliation pending for q4'])}
signed by {partner}
{auditor_firm}
membership number {membership}
firm registration number {firm_reg}
date {rand_date()} place {city}""",

        # Template 4: Short audit opinion
        f"""auditors report
to the members of {company}
we have audited the financial statements of {company} for the year ended 31 march {year}
opinion {opinion_type}
{opinion_text}
key audit matters {' '.join(kam_items[:2])}
auditor {auditor_firm} frn {firm_reg}
partner {partner} m no {membership}
place {city} date {rand_date()}""",
    ]
    
    text = random.choice(templates)
    if random.random() < 0.15:
        text = ocr_noise(text)
    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════
GENERATORS = {
    "insurance_policy": generate_insurance_policy,
    "loan_agreement": generate_loan_agreement,
    "audit_report": generate_audit_report,
}

def main():
    print("=" * 70)
    print("  NEXORA — Synthetic Training Data Generator")
    print("=" * 70)
    
    total_generated = 0
    
    for category, generator in GENERATORS.items():
        output_dir = CLASSIFICATION_DIR / category
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Count existing files
        existing = list(output_dir.glob("doc_*.txt"))
        start_idx = len(existing) + 1
        
        print(f"\n[DIR] Category: {category}")
        print(f"      Existing files: {len(existing)}")
        print(f"      Generating: {NUM_SAMPLES} new samples...")
        
        for i in range(NUM_SAMPLES):
            doc_num = start_idx + i
            filename = f"doc_{doc_num:04d}.txt"
            filepath = output_dir / filename
            
            text = generator()
            filepath.write_text(text, encoding="utf-8")
        
        final_count = len(list(output_dir.glob("doc_*.txt")))
        print(f"      [OK] Done! Total files now: {final_count}")
        total_generated += NUM_SAMPLES
    
    print(f"\n{'=' * 70}")
    print(f"  COMPLETE: Generated {total_generated} files across {len(GENERATORS)} categories")
    print(f"  Location: {CLASSIFICATION_DIR}")
    print(f"{'=' * 70}")
    
    # Print summary of ALL categories
    print(f"\nFULL CLASSIFICATION DATA SUMMARY:")
    print(f"{'=' * 50}")
    total = 0
    for folder in sorted(CLASSIFICATION_DIR.iterdir()):
        if folder.is_dir():
            count = len(list(folder.glob("*.txt")))
            status = "[OK]" if count >= 300 else "[!!]"
            print(f"   {status} {folder.name:<25} {count:>5} files")
            total += count
    print(f"{'=' * 50}")
    print(f"   TOTAL: {total:>30} files")


if __name__ == "__main__":
    main()
