from datetime import date

import pandas as pd

from src.classifier.hybrid import classify
from src.classifier.rules import classify_by_rules
from src.enrich import enrich
from src.exporter import to_csv_bytes, to_excel_bytes
from src.validator import check_balances, validate


def test_rules():
    assert classify_by_rules("UPI/DR/123456789012/SWIGGY/YESB/swiggy@ybl/Payment", "debit")[0] == "Food & Dining"
    assert classify_by_rules("NEFT CR-INFOSYS LIMITED-SALARY APR", "credit")[0] == "Salary"
    assert classify_by_rules("REFUND AMAZON ORDER 1234", "credit")[0] == "Refunds & Cashback"
    assert classify_by_rules("ATM WDL ATM CASH 1234 MG ROAD", "debit")[0] == "ATM Withdrawal"
    assert classify_by_rules("some unknown shop", "debit")[0] is None


def test_ml_handles_merchants_rules_do_not_know():
    txns = [
        {"description": "UPI/DR/412345678901/CAFE COFFEE DAY/YESB/ccd@ybl/Payment", "direction": "debit"},
        {"description": "UPI/DR/412345678901/WELLNESS PHARMACY/HDFC/w@okaxis/Payment", "direction": "debit"},
    ]
    classify(txns)
    assert txns[0]["category"] == "Food & Dining"
    assert txns[1]["category"] == "Healthcare"
    assert all(t["method"].startswith("ml") or t["method"].startswith("rule") for t in txns)
    assert all(0 <= t["confidence"] <= 1 for t in txns)


def test_enrich_upi():
    txn = enrich({"description": "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment"})
    assert txn["mode"] == "UPI"
    assert txn["counterparty"] == "Swiggy"
    assert txn["upi_id"] == "swiggy@ybl"
    assert txn["ref_no"] == "412345678901"


def _rows():
    return [
        {"date": date(2024, 4, 1), "description": "A", "debit": None, "credit": 1000.0, "balance": 6000.0},
        {"date": date(2024, 4, 2), "description": "B", "debit": 500.0, "credit": None, "balance": 5500.0},
        {"date": date(2024, 4, 3), "description": "C", "debit": 200.0, "credit": None, "balance": 9999.0},
        {"date": date(2024, 4, 4), "description": "D", "debit": 100.0, "credit": None, "balance": 5200.0},
    ]


def test_balance_check_flags_wrong_rows():
    rows = _rows()
    rows[2]["balance"], rows[3]["balance"] = 9999.0, 9899.0  # a real jump, not a misread
    problems = check_balances(rows, opening_balance=5000.0)
    assert rows[0]["balance_ok"] and rows[1]["balance_ok"]
    assert rows[2]["balance_ok"] is False
    assert any("Row 3" in p for p in problems)


def test_balance_check_auto_corrects_single_misread():
    rows = _rows()   # row C shows 9999 but rows B and D prove it must be 5300
    check_balances(rows, opening_balance=5000.0)
    assert rows[2]["balance"] == 5300.0
    assert rows[2]["balance_corrected_from"] == 9999.0


def test_duplicates_and_report():
    rows = _rows()
    rows.append(dict(rows[-1]))
    report = validate(rows, {"opening_balance": 5000.0})
    assert any("duplicate" in p for p in report["problems"])
    assert report["total_credit"] == 1000.0


def test_exports():
    df = pd.DataFrame([{**r, "category": "Others", "confidence": 0.5, "needs_review": True,
                        "counterparty": "", "mode": "Other", "balance_ok": True} for r in _rows()])
    csv = to_csv_bytes(df).decode("utf-8-sig")
    assert csv.splitlines()[0].startswith("Date,")
    xlsx = to_excel_bytes(df, {"bank_name": "Test"}, validate(_rows(), {}))
    assert xlsx[:2] == b"PK"  # xlsx files are zip files


def test_rules_and_corrections_skip_model(monkeypatch):
    from src.classifier import hybrid

    monkeypatch.setattr(hybrid, '_load_corrections', lambda: {'SWIGGY __DEBIT__': 'Shopping'})
    def unexpected_predict(*args):
        raise AssertionError('Resolved transactions must not load the ML model')
    monkeypatch.setattr(hybrid.ml_model, 'predict', unexpected_predict)
    rows = classify([
        {'description': 'SWIGGY', 'direction': 'debit'},
        {'description': 'ATM WDL ATM CASH', 'direction': 'debit'},
    ])
    assert [row['category'] for row in rows] == ['Shopping', 'ATM Withdrawal']
    assert rows[0]['method'] == 'learned from user'
    assert classify([]) == []


def test_ml_results_keep_original_row_order(monkeypatch):
    from src.classifier import hybrid

    monkeypatch.setattr(hybrid, '_load_corrections', lambda: {})
    def predict(descriptions, directions):
        assert descriptions == ['unknown shop', 'another unknown shop']
        assert directions == ['debit', 'debit']
        return [('Shopping', 0.8), ('Shopping', 0.2)]
    monkeypatch.setattr(hybrid.ml_model, 'predict', predict)
    rows = classify([
        {'description': 'unknown shop', 'direction': 'debit'},
        {'description': 'SWIGGY', 'direction': 'debit'},
        {'description': 'another unknown shop', 'direction': 'debit'},
    ])
    assert [row['category'] for row in rows] == ['Shopping', 'Food & Dining', 'Others']
    assert [row['needs_review'] for row in rows] == [False, False, True]
