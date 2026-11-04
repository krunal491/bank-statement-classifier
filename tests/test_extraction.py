"""End-to-end tests on the sample statements in samples/."""

from pathlib import Path

import pytest

from src.pdf_reader import PasswordRequiredError
from src.pipeline import process_many, process_statement

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


def run(name, password=None):
    return process_statement((SAMPLES / name).read_bytes(), password, name)


@pytest.mark.parametrize("name, bank, ifsc", [
    ("sbi_text.pdf", "State Bank of India", "SBIN0001234"),
    ("hdfc_text.pdf", "HDFC Bank", "HDFC0000123"),
    ("icici_text.pdf", "ICICI Bank", "ICIC0004321"),
    ("axis_text.pdf", "Axis Bank", "UTIB0000456"),
    ("kotak_text.pdf", "Kotak Mahindra Bank", "KKBK0000789"),
])
def test_text_pdfs_from_five_banks(name, bank, ifsc):
    result = run(name)
    account, df, report = result["account"], result["transactions"], result["report"]
    assert account["pdf_type"] == "text"
    assert account["bank_name"] == bank
    assert account["ifsc"] == ifsc
    assert account["account_number"]
    assert account["account_holder"]
    assert len(df) >= 40
    # every single balance must add up on clean text PDFs
    assert report["balance_check_pass_rate"] == 100.0
    assert df["category"].notna().all()


def test_scanned_pdf_uses_ocr():
    result = run("hdfc_scanned.pdf")
    assert result["account"]["pdf_type"] == "image"
    assert len(result["transactions"]) >= 40
    assert result["report"]["balance_check_pass_rate"] >= 90


def test_mixed_pdf():
    result = run("icici_mixed.pdf")
    assert result["account"]["pdf_type"] == "mixed"
    assert result["account"]["page_types"][0] == "text"
    assert "image" in result["account"]["page_types"]


def test_locked_pdf_needs_password():
    with pytest.raises(PasswordRequiredError):
        run("axis_locked.pdf")
    with pytest.raises(PasswordRequiredError):
        run("axis_locked.pdf", "wrong")
    assert len(run("axis_locked.pdf", "AXIS1234")["transactions"]) > 0


def test_wrapped_descriptions_are_joined():
    df = run("sbi_text.pdf")["transactions"]
    # long UPI narrations wrap onto 2 lines in the PDF; they must be one description
    upi = df[df["description"].str.startswith("UPI/DR/")]
    assert len(upi) > 0
    assert upi["description"].str.endswith("Payment").all()


def test_single_amount_column_with_dr_cr():
    df = run("kotak_text.pdf")["transactions"]
    salary = df[df["category"] == "Salary"]
    assert salary["credit"].notna().all() and salary["debit"].isna().all()


def test_merging_overlapping_files_removes_duplicates():
    data = (SAMPLES / "axis_text.pdf").read_bytes()
    out = process_many([("a.pdf", data, None), ("b.pdf", data, None)])
    assert out["duplicates_removed"] == len(out["results"][0]["transactions"])


def test_recurring_payments_found():
    df = run("hdfc_text.pdf")["transactions"]
    recurring = set(df[df["is_recurring"]]["category"])
    assert {"Salary", "Rent", "EMI & Loans"} <= recurring
