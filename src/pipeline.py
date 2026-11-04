"""
The whole process in one place. The web app and the command line both call
`process_statement()` (one PDF) or `process_many()` (several PDFs).

    PDF bytes
      -> read_pdf()                 text or OCR, words with positions
      -> extract_account_details()  name, account no, IFSC, bank, period
      -> extract_transactions()     date, description, debit, credit, balance
      -> validate()                 balance check, duplicates, date checks
      -> enrich()                   mode (UPI/NEFT/...), counterparty, reference
      -> classify()                 rules + ML -> category and confidence
      -> insights                   recurring payments, summaries
"""

import pandas as pd

from src import insights
from src.account_parser import extract_account_details
from src.classifier.hybrid import classify
from src.enrich import enrich
from src.pdf_reader import read_pdf
from src.transaction_parser import extract_transactions, fix_dates
from src.validator import validate


def process_statement(pdf_bytes, password=None, file_name="statement.pdf"):
    """Process one PDF. Returns a dict with account, transactions (DataFrame) and report."""
    pdf = read_pdf(pdf_bytes, password)
    account = extract_account_details(pdf["full_text"])
    account["pdf_type"] = pdf["pdf_type"]
    account["page_types"] = [p["type"] for p in pdf["pages"]]
    account["file_name"] = file_name

    transactions = extract_transactions(pdf["pages"], account.get("opening_balance"))
    fix_dates(transactions, account.get("period_from"), account.get("period_to"))
    report = validate(transactions, account)

    for txn in transactions:
        enrich(txn)
        txn["source_file"] = file_name
    classify(transactions)

    df = to_dataframe(transactions)
    df = insights.mark_recurring(df, insights.find_recurring(df))
    report["needs_review"] = int(df["needs_review"].sum()) if not df.empty else 0
    return {"account": account, "transactions": df, "report": report}


def process_many(files):
    """
    Process several PDFs and merge them into one table.
    `files` is a list of (file_name, pdf_bytes, password).
    Overlapping statements are handled by removing duplicate rows.
    """
    results = [process_statement(data, password, name) for name, data, password in files]
    merged = pd.concat([r["transactions"] for r in results], ignore_index=True)
    before = len(merged)
    if not merged.empty:
        merged = (
            merged.sort_values(["date"], kind="stable")
            .drop_duplicates(subset=["date", "description", "debit", "credit", "balance"])
            .reset_index(drop=True)
        )
        merged = insights.mark_recurring(merged, insights.find_recurring(merged))
    return {
        "results": results,
        "merged": merged,
        "duplicates_removed": before - len(merged),
    }


def reclassify(df):
    """Classify a table again (used after the user saved corrections)."""
    records = df.to_dict("records")
    classify(records)
    out = pd.DataFrame(records, index=df.index)
    return insights.mark_recurring(out, insights.find_recurring(out))


def combined_report(results, merged):
    """One summary for several statements (used for the Excel export)."""
    problems = []
    for r in results:
        problems += [f"[{r['account']['file_name']}] {p}" for p in r["report"]["problems"]]
    checked = merged["balance_ok"].dropna() if not merged.empty else []
    return {
        "opening_balance": results[0]["report"]["opening_balance"] if results else None,
        "closing_balance": results[-1]["report"]["closing_balance"] if results else None,
        "total_debit": round(float(merged["debit"].fillna(0).sum()), 2) if not merged.empty else 0,
        "total_credit": round(float(merged["credit"].fillna(0).sum()), 2) if not merged.empty else 0,
        "transaction_count": len(merged),
        "balance_check_pass_rate": round(100 * float(checked.astype(bool).mean()), 1) if len(checked) else None,
        "problems": problems,
    }


def to_dataframe(transactions):
    columns = [
        "date", "value_date", "description", "counterparty", "mode", "upi_id", "ref_no",
        "debit", "credit", "balance", "direction", "category", "confidence", "method",
        "needs_review", "balance_ok", "is_duplicate", "page", "source_file",
    ]
    df = pd.DataFrame(transactions)
    for col in columns:
        if col not in df.columns:
            df[col] = None
    df = df[columns]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    for col in ("debit", "credit", "balance"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
