"""
Create realistic FAKE bank statements in different bank layouts.

Run:  python -m scripts.generate_samples

It writes PDFs to the samples/ folder:
  - <bank>_text.pdf      normal (text-based) PDFs for 5 bank layouts
  - <bank>_scanned.pdf   image-only PDFs (like a scan), slightly tilted and noisy
  - icici_mixed.pdf      first page is text, the other pages are scanned
  - axis_locked.pdf      password protected (password: AXIS1234)

All names, numbers and transactions are made up.
"""

import io
import random
import re
from datetime import date, timedelta
from pathlib import Path

import pymupdf as fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageFilter
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from scripts.synthetic import make_transaction

OUT_DIR = Path(__file__).resolve().parent.parent / "samples"

# ---------------------------------------------------------------------------
# How each bank's statement looks
# ---------------------------------------------------------------------------
# Each column: (key, header text, left x, width, alignment)
BANKS = {
    "sbi": {
        "bank": "SBI", "title": "STATE BANK OF INDIA", "ifsc": "SBIN0001234", "page": A4,
        "date_format": "%d %b %Y", "branch": "MG Road, Bengaluru",
        "columns": [
            ("date", "Txn Date", 30, 52, "left"),
            ("value_date", "Value Date", 84, 52, "left"),
            ("desc", "Description", 138, 170, "left"),
            ("ref", "Ref No.", 312, 62, "left"),
            ("debit", "Debit", 376, 62, "right"),
            ("credit", "Credit", 440, 62, "right"),
            ("balance", "Balance", 504, 66, "right"),
        ],
    },
    "hdfc": {
        "bank": "HDFC", "title": "HDFC BANK LTD", "ifsc": "HDFC0000123", "page": A4,
        "date_format": "%d/%m/%y", "branch": "Koramangala, Bengaluru",
        "columns": [
            ("date", "Date", 30, 42, "left"),
            ("desc", "Narration", 74, 190, "left"),
            ("ref", "Chq./Ref.No.", 268, 66, "left"),
            ("value_date", "Value Dt", 336, 40, "left"),
            ("debit", "Withdrawal Amt.", 378, 62, "right"),
            ("credit", "Deposit Amt.", 442, 60, "right"),
            ("balance", "Closing Balance", 504, 66, "right"),
        ],
    },
    "icici": {
        "bank": "ICICI", "title": "ICICI BANK LIMITED", "ifsc": "ICIC0004321", "page": landscape(A4),
        "date_format": "%d/%m/%Y", "branch": "Andheri East, Mumbai",
        "columns": [
            ("sno", "S No.", 30, 28, "left"),
            ("value_date", "Value Date", 60, 60, "left"),
            ("date", "Transaction Date", 124, 68, "left"),
            ("ref", "Cheque Number", 196, 70, "left"),
            ("desc", "Transaction Remarks", 270, 250, "left"),
            ("debit", "Withdrawal Amount (INR)", 524, 92, "right"),
            ("credit", "Deposit Amount (INR)", 620, 92, "right"),
            ("balance", "Balance (INR)", 716, 90, "right"),
        ],
    },
    "axis": {
        "bank": "AXIS", "title": "AXIS BANK", "ifsc": "UTIB0000456", "page": A4,
        "date_format": "%d-%m-%Y", "branch": "Banjara Hills, Hyderabad",
        "columns": [
            ("date", "Tran Date", 30, 52, "left"),
            ("ref", "Chq No", 84, 40, "left"),
            ("desc", "Particulars", 126, 210, "left"),
            ("debit", "Debit", 340, 62, "right"),
            ("credit", "Credit", 404, 62, "right"),
            ("balance", "Balance", 468, 66, "right"),
            ("branch", "Init. Br", 540, 30, "left"),
        ],
    },
    "kotak": {
        "bank": "KOTAK", "title": "KOTAK MAHINDRA BANK", "ifsc": "KKBK0000789", "page": A4,
        "date_format": "%d-%b-%Y", "branch": "Viman Nagar, Pune",
        "columns": [
            ("date", "Date", 30, 56, "left"),
            ("desc", "Narration", 88, 220, "left"),
            ("ref", "Chq/Ref No", 312, 70, "left"),
            ("amount", "Amount", 384, 70, "right"),
            ("drcr", "Dr / Cr", 460, 34, "left"),
            ("balance", "Balance", 498, 72, "right"),
        ],
    },
}

CUSTOMERS = {
    "sbi": ("RAHUL SHARMA", "00000034567890123"),
    "hdfc": ("PRIYA NAIR", "50100234567812"),
    "icici": ("AMIT KULKARNI", "123401234567"),
    "axis": ("SNEHA REDDY", "918010012345678"),
    "kotak": ("VIKRAM JOSHI", "4512367890"),
}

# Rough amount ranges for each category (in rupees).
AMOUNTS = {
    "Food & Dining": (120, 1800), "Groceries": (300, 4500), "Shopping": (400, 12000),
    "Transport & Fuel": (80, 3500), "Travel": (900, 15000), "Bills & Utilities": (199, 3200),
    "Entertainment & Subscriptions": (149, 1200), "Healthcare": (150, 6000), "Education": (500, 25000),
    "Investments": (1000, 10000), "Insurance": (1500, 12000), "ATM Withdrawal": (500, 10000),
    "Transfers": (200, 8000), "Bank Charges": (15, 590), "Interest": (40, 900),
    "Refunds & Cashback": (25, 1500), "Taxes": (1000, 15000),
}
RANDOM_CATEGORIES = list(AMOUNTS.keys())


def build_transactions(rng, bank, start, months=3):
    """Make ~3 months of transactions, including monthly recurring payments."""
    rows = []
    salary = rng.choice([65000, 78000, 92000, 120000])
    rent = rng.choice([18000, 22000, 25000])
    emi = rng.choice([8450, 12300, 15999])
    for m in range(months):
        month_start = date(start.year + (start.month - 1 + m) // 12, (start.month - 1 + m) % 12 + 1, 1)
        mon = month_start.strftime("%b").upper()
        fixed = [
            (1, "Salary", salary), (3, "Rent", rent), (5, "EMI & Loans", emi),
            (7, "Investments", 5000), (15, "Entertainment & Subscriptions", 649),
        ]
        for day, cat, amount in fixed:
            r = random.Random(f"{bank}-{cat}")  # same description every month -> recurring
            desc, kind = make_transaction(r, cat, bank.upper(), mon)
            if cat == "Salary":
                desc = desc.replace("APR", mon)
            rows.append((month_start + timedelta(days=day - 1), desc, kind, float(amount)))
        for _ in range(rng.randint(10, 14)):
            cat = rng.choice(RANDOM_CATEGORIES)
            desc, kind = make_transaction(rng, cat, bank.upper(), mon)
            low, high = AMOUNTS[cat]
            amount = round(rng.uniform(low, high), 2)
            if cat in ("ATM Withdrawal", "Investments"):
                amount = float(round(amount, -2))
            day = rng.randint(1, 28)
            rows.append((month_start + timedelta(days=day - 1), desc, kind, amount))
    rows.sort(key=lambda r: r[0])
    return rows


def money(value):
    """Format like Indian banks: 1,23,456.78"""
    sign = "-" if value < 0 else ""
    whole, frac = f"{abs(value):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = re.sub(r"(\d)(?=(\d{2})+$)", r"\1,", head)
        whole = f"{head},{tail}"
    return f"{sign}{whole}.{frac}"


def wrap(text, max_chars):
    """Split long narrations into lines, breaking after '/', '-', '*' or spaces."""
    pieces = re.findall(r"[^/\-* ]*[/\-* ]?", text)
    lines, current = [], ""
    for piece in pieces:
        if not piece:
            continue
        if len(current) + len(piece) > max_chars and current:
            lines.append(current.rstrip())
            current = ""
        while len(piece) > max_chars:  # a single very long piece
            lines.append(piece[:max_chars])
            piece = piece[max_chars:]
        current += piece
    if current.strip():
        lines.append(current.rstrip())
    return lines


def draw_statement(path, key, rng):
    cfg = BANKS[key]
    name, account = CUSTOMERS[key]
    start = date(2024, 4, 1)
    txns = build_transactions(rng, key, start)
    opening = round(rng.uniform(15000, 60000), 2)
    end = date(2024, 6, 30)
    fmt = cfg["date_format"]

    width, height = cfg["page"]
    c = canvas.Canvas(str(path), pagesize=cfg["page"])
    font, size = "Helvetica", 7.5
    line_h = 10
    columns = cfg["columns"]
    desc_col = next(col for col in columns if col[0] == "desc")
    max_chars = int(desc_col[3] / (size * 0.52))

    def header(first_page):
        y = height - 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, y, cfg["title"])
        c.setFont(font, 8)
        c.drawRightString(width - 30, y, "Account Statement")
        y -= 22
        if first_page:
            details = [
                f"Account Name : {name}",
                f"Account Number : {account}",
                f"IFSC Code : {cfg['ifsc']}",
                f"Branch : {cfg['branch']}",
                f"Customer ID : {rng.randint(10000000, 99999999)}",
                f"Statement Period : {start.strftime(fmt)} to {end.strftime(fmt)}",
                f"Opening Balance : {money(opening)}",
            ]
            for text in details:
                c.drawString(30, y, text)
                y -= 12
            y -= 6
        c.setFont("Helvetica-Bold", 7.5)
        for col_key, title, x, w, align in columns:
            if align == "right":
                c.drawRightString(x + w, y, title)
            else:
                c.drawString(x, y, title)
        c.line(30, y - 4, width - 25, y - 4)
        c.setFont(font, size)
        return y - 16

    page_no = 1
    y = header(True)
    balance = opening
    # Skip spends the customer can't afford, so the balance stays positive.
    affordable = []
    running = opening
    for row in txns:
        if row[2] == "debit" and running - row[3] < 1000:
            continue
        running += -row[3] if row[2] == "debit" else row[3]
        affordable.append(row)
    for sno, (day, desc, kind, amount) in enumerate(affordable, start=1):
        balance = round(balance - amount if kind == "debit" else balance + amount, 2)
        desc_lines = wrap(desc, max_chars)
        needed = line_h * len(desc_lines) + 4
        if y - needed < 50:
            c.drawCentredString(width / 2, 25, f"Page {page_no}")
            c.showPage()
            page_no += 1
            y = header(False)
        values = {
            "sno": str(sno),
            "date": day.strftime(fmt),
            "value_date": day.strftime(fmt),
            "ref": str(rng.randint(100000, 999999)) if rng.random() < 0.3 else "",
            "debit": money(amount) if kind == "debit" else "",
            "credit": money(amount) if kind == "credit" else "",
            "amount": money(amount),
            "drcr": "DR" if kind == "debit" else "CR",
            "balance": money(balance),
            "branch": str(rng.randint(100, 999)),
        }
        for col_key, _, x, w, align in columns:
            if col_key == "desc":
                for i, text in enumerate(desc_lines):
                    c.drawString(x, y - i * line_h, text)
                continue
            text = values[col_key]
            if align == "right":
                c.drawRightString(x + w, y, text)
            else:
                c.drawString(x, y, text)
        y -= needed

    c.setFont("Helvetica-Bold", 8)
    c.drawString(30, y - 6, f"Closing Balance : {money(balance)}")
    c.setFont(font, 7)
    c.drawString(30, y - 22, "This is a computer generated statement and does not require a signature.")
    c.drawCentredString(width / 2, 25, f"Page {page_no}")
    c.save()


def make_scanned(src, dst, rng, dpi=200, only_pages=None):
    """Turn a text PDF into an image-only PDF that looks like a scan."""
    source = fitz.open(src)
    out = fitz.open()
    for i, page in enumerate(source):
        if only_pages is not None and i not in only_pages:
            out.insert_pdf(source, from_page=i, to_page=i)
            continue
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")
        img = img.rotate(rng.uniform(-0.8, 0.8), expand=False, fillcolor=255, resample=Image.BICUBIC)
        arr = np.array(img).astype(np.int16)
        arr += np.random.default_rng(i).normal(0, 12, arr.shape).astype(np.int16)  # scanner noise
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        new_page = out.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=buf.getvalue())
    out.save(dst)


def lock_pdf(src, dst, password):
    reader = PdfReader(src)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open(dst, "wb") as f:
        writer.write(f)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for key in BANKS:
        draw_statement(OUT_DIR / f"{key}_text.pdf", key, random.Random(key))
        print("created", f"{key}_text.pdf")
    for key in ("sbi", "hdfc"):
        make_scanned(OUT_DIR / f"{key}_text.pdf", OUT_DIR / f"{key}_scanned.pdf", random.Random(key))
        print("created", f"{key}_scanned.pdf")
    make_scanned(OUT_DIR / "icici_text.pdf", OUT_DIR / "icici_mixed.pdf", random.Random(1),
                 only_pages=range(1, 99))
    print("created icici_mixed.pdf")
    lock_pdf(OUT_DIR / "axis_text.pdf", OUT_DIR / "axis_locked.pdf", "AXIS1234")
    print("created axis_locked.pdf (password AXIS1234)")


if __name__ == "__main__":
    main()
