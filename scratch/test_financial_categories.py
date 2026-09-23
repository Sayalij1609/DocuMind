import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath("backend"))

from app.ml.classification.heuristics import FinancialHeuristicClassifier
from app.ml.extraction.registry import ExtractionStrategyRegistry
from app.validation.rules import (
    create_bank_statement_validation_rules,
    create_salary_slip_validation_rules,
    create_invoice_validation_rules,
    create_utility_bill_validation_rules,
)
from app.validation.base import ValidationEngine

def run_tests():
    print("=== 1. Testing Financial Classification ===")
    clf = FinancialHeuristicClassifier()
    test_cases = {
        "bank_statement": "State Bank of India Account Statement A/c No: 12345678901 Opening Balance: 50,000.00 Total Deposits: 25,000.00 Total Withdrawals: 10,000.00 Closing Balance: 65,000.00 IFSC: SBIN0001234",
        "salary_slip": "Infosys Ltd Salary Slip / Payslip for August 2026 Employee ID: INF-1092 Basic Salary: 45,000 Gross Salary: 65,000 Total Deductions: 7,400 Net Pay: 57,600",
        "utility_bill": "Maharashtra State Electricity Distribution Co Ltd Meter No: 88721 Units Consumed: 340 kWh Due Date: 15/10/2026 Total Amount Due: 2,850",
        "receipt": "Starbucks Coffee Payment Receipt POS Terminal #4 Cashier: Alice Total Paid: 450 Paid by Cash Change Due: 50 Thank you visit again",
        "purchase_order": "Purchase Order PO Number: PO-9982 Order Date: 12/09/2026 Deliver To: Acme Warehouse Bangalore Total Amount: 1,20,000",
        "tax_document": "Form 16 Certificate under section 203 of Income-tax Act Assessment Year 2026-27 PAN: ABCDE1234F Gross Total Income: 8,50,000 Tax Deducted at Source TDS",
        "insurance": "Star Health Insurance Policy Schedule Policy Number: POL-77889 Sum Insured: 5,00,000 Premium Amount: 14,500 Period of Insurance: 2026-2027",
        "credit_debit_note": "Credit Note CR-4432 against Invoice INV-1090 Reason: Goods returned by customer Revised Amount: 4,500 Tax adjustment",
    }

    for expected, sample in test_cases.items():
        res = clf.classify(sample)
        assert res is not None, f"Failed to classify: {expected}"
        assert res.document_type == expected, f"Expected {expected}, got {res.document_type}"
        print(f"  [PASS] {expected} -> detected with {res.confidence*100:.1f}% confidence")

    print("\n=== 2. Testing Extraction Registry ===")
    registry = ExtractionStrategyRegistry()
    for cat in ["bank_statement", "salary_slip", "utility_bill", "receipt", "purchase_order", "tax_document", "insurance"]:
        ext = registry.get(cat)
        assert ext is not None, f"No extractor for {cat}"
        sample = test_cases.get(cat, "Sample text")
        res = ext.extract(sample)
        print(f"  [PASS] {cat}: Extractor {type(ext).__name__} extracted {len(res.fields)} fields: {list(res.fields.keys())}")

    print("\n=== 3. Testing Domain Validation Engines ===")
    # Bank Statement validation
    bank_engine = ValidationEngine(rules=create_bank_statement_validation_rules())
    bank_fields = {
        "account_number": {"value": "12345678901"},
        "opening_balance": {"value": "50000.00"},
        "total_deposits": {"value": "25000.00"},
        "total_withdrawals": {"value": "10000.00"},
        "closing_balance": {"value": "65000.00"},
    }
    bank_res = bank_engine.validate("doc-1", "bank_statement", bank_fields)
    assert bank_res.status.value in ["VALID", "valid", "NORMAL", "normal"], f"Bank validation status: {bank_res.status.value}"
    print(f"  [PASS] Bank Statement Validation: {bank_res.status.value} (Rules checked: {len(bank_res.results)})")

    # Salary Slip validation
    salary_engine = ValidationEngine(rules=create_salary_slip_validation_rules())
    salary_fields = {
        "employee_id": {"value": "EMP-101"},
        "gross_salary": {"value": "65000.00"},
        "total_deductions": {"value": "7400.00"},
        "net_salary": {"value": "57600.00"},
    }
    salary_res = salary_engine.validate("doc-2", "salary_slip", salary_fields)
    assert salary_res.status.value in ["VALID", "valid", "NORMAL", "normal"], f"Salary validation status: {salary_res.status.value}"
    print(f"  [PASS] Salary Slip Validation: {salary_res.status.value} (Rules checked: {len(salary_res.results)})")

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
