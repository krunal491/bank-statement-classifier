"""
Final step: export the results to Excel (.xlsx) and CSV (.csv).

The Excel file has several sheets:
  Transactions | Account Summary | Category Summary | Monthly Summary |
  Recurring Payments | Top Merchants | Data Quality
"""

import io

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from src import insights

# Columns shown to the user, in this order, with friendly names.
EXPORT_COLUMNS = {
    "date": "Date",
    "value_date": "Value Date",
    "description": "Description",
    "counterparty": "Counterparty",
    "mode": "Mode",
    "ref_no": "Reference No",
    "debit": "Debit",
    "credit": "Credit",
    "balance": "Balance",
    "category": "Category",
    "confidence": "Confidence",
    "method": "Classified By",
    "needs_review": "Needs Review",
    "is_recurring": "Recurring",
    "balance_ok": "Balance Check OK",
    "source_file": "Source File",
}

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
REVIEW_FILL = PatternFill("solid", fgColor="FFF2CC")   # light yellow
ERROR_FILL = PatternFill("solid", fgColor="F8CBAD")    # light red


def to_export_frame(df):
    """Pick and rename columns for export."""
    cols = [c for c in EXPORT_COLUMNS if c in df.columns]
    return df[cols].rename(columns=EXPORT_COLUMNS)


def to_csv_bytes(df):
    # utf-8-sig so Excel opens the ₹ sign and Indian names correctly
    return to_export_frame(df).to_csv(index=False).encode("utf-8-sig")


def _style_sheet(ws, money_columns=()):
    """Bold blue header, sensible column widths, money format."""
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    for idx, column in enumerate(ws.columns, start=1):
        values = [str(c.value) if c.value is not None else "" for c in column]
        width = min(max(len(v) for v in values) + 2, 60)
        ws.column_dimensions[get_column_letter(idx)].width = max(width, 10)
        if values[0] in money_columns:
            for cell in column[1:]:
                cell.number_format = "#,##0.00"


def to_excel_bytes(df, account, report):
    """Build the full Excel workbook and return it as bytes."""
    buffer = io.BytesIO()
    export = to_export_frame(df)
    money = {"Debit", "Credit", "Balance", "money_in", "money_out", "net_savings",
             "typical_amount", "total_spent", "Value"}

    account_rows = [
        ("Bank", account.get("bank_name")),
        ("Account Holder", account.get("account_holder")),
        ("Account Number", account.get("account_number")),
        ("IFSC", account.get("ifsc")),
        ("Branch", account.get("branch")),
        ("Customer ID", account.get("customer_id")),
        ("Statement From", account.get("period_from")),
        ("Statement To", account.get("period_to")),
        ("PDF Type", account.get("pdf_type")),
        ("Opening Balance", report.get("opening_balance")),
        ("Closing Balance", report.get("closing_balance")),
        ("Total Debits", report.get("total_debit")),
        ("Total Credits", report.get("total_credit")),
        ("Transactions", report.get("transaction_count")),
        ("Balance Check Pass Rate %", report.get("balance_check_pass_rate")),
    ]
    summary = pd.DataFrame(account_rows, columns=["Field", "Value"])
    quality = pd.DataFrame({"Issue": report.get("problems") or ["No problems found"]})

    sheets = {
        "Transactions": export,
        "Account Summary": summary,
        "Category Summary": insights.category_summary(df),
        "Monthly Summary": insights.monthly_summary(df),
        "Recurring Payments": insights.find_recurring(df),
        "Top Merchants": insights.top_merchants(df),
        "Data Quality": quality,
    }

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            _style_sheet(writer.sheets[name], money)

        # Highlight rows: yellow = please review the category, red = balance problem
        ws = writer.sheets["Transactions"]
        headers = [c.value for c in ws[1]]
        review_col = headers.index("Needs Review") + 1 if "Needs Review" in headers else None
        balance_col = headers.index("Balance Check OK") + 1 if "Balance Check OK" in headers else None
        for row in ws.iter_rows(min_row=2):
            fill = None
            if balance_col and row[balance_col - 1].value is False:
                fill = ERROR_FILL
            elif review_col and row[review_col - 1].value is True:
                fill = REVIEW_FILL
            if fill:
                for cell in row:
                    cell.fill = fill
    return buffer.getvalue()
