"""
Make descriptions easier to understand.

Bank descriptions look like "UPI/DR/412345678901/SWIGGY/YESB/swiggy@ybl/Payment".
From that we pull out:
  - mode         : how the money moved (UPI, NEFT, IMPS, ATM, Card, ...)
  - counterparty : who the money went to / came from (SWIGGY)
  - upi_id       : swiggy@ybl
  - reference    : 412345678901
"""

import re

MODES = [
    ("UPI", r"\bUPI\b|UPI[/\-]"),
    ("NEFT", r"\bNEFT\b"),
    ("IMPS", r"\bIMPS\b"),
    ("RTGS", r"\bRTGS\b"),
    ("ATM", r"\bATM\b|\bNWD\b|CASH WITHDRAWAL"),
    ("Card", r"\bPOS\b|DEBIT CARD|\bECOM\b|CARD PURCHASE"),
    ("NACH/Auto-debit", r"\bNACH\b|\bACH\b|\bECS\b|SI[ -]DEBIT|AUTO ?DEBIT|MANDATE"),
    ("Cheque", r"\bCHQ\b|CHEQUE|\bCLG\b|CLEARING"),
    ("Interest", r"INTEREST|INT\.PD|\bINT\b"),
    ("Charges", r"CHARGE|\bFEE\b|\bGST\b"),
    ("Cash Deposit", r"CASH DEP|BY CASH"),
]

# Words that are not names (bank codes, directions, filler words)
NOT_A_NAME = {
    "UPI", "DR", "CR", "P2A", "P2M", "PAYMENT", "UPI PAYMENT", "NEFT", "IMPS", "RTGS", "PAY",
    "SENT", "RECEIVED", "TRANSFER", "TO", "BY", "FROM", "YESB", "HDFC", "ICIC", "UTIB", "SBIN",
    "PYTM", "KKBK", "AXIS", "NA", "REF", "TXN", "POS", "ECOM PUR", "ACH D", "NACH DR",
}


def detect_mode(description):
    for mode, pattern in MODES:
        if re.search(pattern, description, re.IGNORECASE):
            return mode
    return "Other"


def extract_upi_id(description):
    match = re.search(r"([A-Za-z0-9.\-_]+@[A-Za-z]+)", description)
    return match.group(1).lower() if match else ""


def extract_reference(description):
    """UPI/IMPS references are usually 12 digits."""
    match = re.search(r"(?<!\d)(\d{12})(?!\d)", description)
    if match:
        return match.group(1)
    match = re.search(r"(?<!\d)(\d{8,16})(?!\d)", description)
    return match.group(1) if match else ""


def extract_counterparty(description):
    """
    Guess the person/shop on the other side of the transaction.
    We split the description on '/', '-' and '*' and pick the first piece
    that looks like a name (letters, not a known code word).
    """
    text = description.upper()
    text = re.sub(r"^(POS\s+\S+|DEBIT CARD PURCHASE|ECOM PUR|NACH DR|ACH D-|SALARY CREDIT|TO TRANSFER-|BY TRANSFER-|LOAN REPAYMENT)\s*", "", text)
    pieces = re.split(r"[/\-*]", text)
    for piece in pieces:
        piece = piece.strip()
        piece = re.sub(r"\b(DR|CR|NEFT|IMPS|UPI|EMI)\b", "", piece).strip()
        if "@" in piece or not piece:
            continue
        letters = sum(c.isalpha() for c in piece)
        if letters < 3 or piece in NOT_A_NAME:
            continue
        if re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", piece):  # an IFSC code
            continue
        # Drop trailing words that are clearly not part of a name.
        piece = re.sub(r"\b(PAYMENT|BANGALORE|MUMBAI|UPI PAYMENT|SELF TRANSFER|HOUSE RENT)\b.*$", "", piece).strip()
        piece = re.sub(r"^\d+\s|\s\d+$", "", piece).strip()
        piece = re.sub(r"^(REFUND|CASHBACK|REVERSAL( UPI)?)\s+|\s+ORDER$", "", piece).strip()
        if sum(c.isalpha() for c in piece) >= 3:
            return piece.title()
    return ""


def enrich(transaction):
    """Add mode, counterparty, upi_id and reference to a transaction dict."""
    desc = transaction.get("description", "")
    transaction["mode"] = detect_mode(desc)
    # For ATM cash, interest and bank charges there is no real "other party".
    no_party = transaction["mode"] in ("ATM", "Interest", "Charges")
    transaction["counterparty"] = "" if no_party else extract_counterparty(desc)
    transaction["upi_id"] = extract_upi_id(desc)
    if not transaction.get("ref_no"):
        transaction["ref_no"] = extract_reference(desc)
    return transaction
