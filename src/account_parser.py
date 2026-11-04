"""
Step 2 of the pipeline: find the account holder details and the bank.

We search the statement text with regular expressions (patterns), e.g.
"Account Number : 1234567890" or "IFSC Code: SBIN0001234".
"""

import re

from src.utils import clean_text, parse_amount, parse_date

# IFSC codes start with 4 letters (the bank), then 0, then 6 letters/digits.
# The first 4 letters tell us the bank.
IFSC_PREFIX_TO_BANK = {
    "SBIN": "State Bank of India",
    "HDFC": "HDFC Bank",
    "ICIC": "ICICI Bank",
    "UTIB": "Axis Bank",
    "KKBK": "Kotak Mahindra Bank",
    "PUNB": "Punjab National Bank",
    "BARB": "Bank of Baroda",
    "CNRB": "Canara Bank",
    "UBIN": "Union Bank of India",
    "IDIB": "Indian Bank",
    "YESB": "Yes Bank",
    "INDB": "IndusInd Bank",
    "IDFB": "IDFC First Bank",
    "FDRL": "Federal Bank",
    "BKID": "Bank of India",
}

# Bank names as they appear in the statement heading.
BANK_NAME_PATTERNS = {
    "State Bank of India": r"state\s+bank\s+of\s+india|\bSBI\b",
    "HDFC Bank": r"\bHDFC\s+BANK",
    "ICICI Bank": r"\bICICI\s+BANK",
    "Axis Bank": r"\bAXIS\s+BANK",
    "Kotak Mahindra Bank": r"\bKOTAK",
    "Punjab National Bank": r"punjab\s+national\s+bank",
    "Bank of Baroda": r"bank\s+of\s+baroda",
    "Canara Bank": r"canara\s+bank",
    "Yes Bank": r"\bYES\s+BANK",
    "IDFC First Bank": r"IDFC\s+FIRST",
}

IFSC_RE = re.compile(r"\b([A-Z]{4}0[A-Z0-9]{6})\b")

FIELD_PATTERNS = {
    "account_holder": r"(?:account\s*holder(?:'s)?\s*name|account\s*name|customer\s*name|a/c\s*name|name)\s*[:\-]\s*(?:mr\.?|mrs\.?|ms\.?)?\s*([A-Za-z][A-Za-z .']{2,60})",
    "account_number": r"(?:account\s*(?:no|number|#)|a/c\s*(?:no|number)|acct\s*no)\.?\s*[:\-]?\s*([0-9X*]{6,20})",
    "customer_id": r"(?:customer\s*id|cust\s*id|cif\s*(?:no|number)?)\.?\s*[:\-]?\s*([0-9]{5,15})",
    "branch": r"branch(?:\s*name)?\s*[:\-]\s*([A-Za-z0-9 ,.\-]{3,60})",
    "micr": r"micr(?:\s*code)?\s*[:\-]?\s*(\d{9})",
}

PERIOD_RE = re.compile(
    r"(?:statement\s*period|period|from)\s*[:\-]?\s*(.+?)\s+(?:to|-)\s+(.+?)$",
    re.IGNORECASE | re.MULTILINE,
)
BALANCE_RE = {
    "opening_balance": re.compile(r"opening\s*balance\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+\.\d{2}(?:\s?(?:Cr|Dr))?)", re.I),
    "closing_balance": re.compile(r"closing\s*balance\s*[:\-]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+\.\d{2}(?:\s?(?:Cr|Dr))?)", re.I),
}


# OCR can misread the "0" in an IFSC code as O, G, Q or D.
OCR_IFSC_RE = re.compile(r"IFSC(?:\s*code)?\s*[:\-]?\s*([A-Z]{4})[0OGQD]([A-Z0-9]{6})\b", re.IGNORECASE)


def find_ifsc(text):
    """Find the IFSC code, also when OCR misread its 5th character."""
    match = IFSC_RE.search(text)
    if match:
        return match.group(1)
    match = OCR_IFSC_RE.search(text)
    if match:
        return f"{match.group(1).upper()}0{match.group(2).upper()}"
    return None


def detect_bank(text):
    """Find the bank from the IFSC code first (most reliable), then from its name."""
    ifsc = find_ifsc(text)
    if ifsc and ifsc[:4] in IFSC_PREFIX_TO_BANK:
        return IFSC_PREFIX_TO_BANK[ifsc[:4]]
    for bank, pattern in BANK_NAME_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return bank
    return "Unknown Bank"


def _parse_period_date(text):
    """Dates in the period line may be followed by other words; try the first 1-3 words."""
    words = text.split()
    for size in (1, 3, 2):
        parsed = parse_date(" ".join(words[:size]))
        if parsed:
            return parsed
    return None


def extract_account_details(text):
    """Return a dict with the account details we could find (missing ones are None)."""
    # Only look at the top part of the statement (before the table gets long).
    head = "\n".join(text.splitlines()[:60])
    details = {"bank_name": detect_bank(head)}

    for field, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, head, re.IGNORECASE)
        details[field] = clean_text(match.group(1)).title() if match and field in ("account_holder", "branch") else (
            clean_text(match.group(1)) if match else None)

    details["ifsc"] = find_ifsc(head)

    period = PERIOD_RE.search(head)
    details["period_from"] = _parse_period_date(period.group(1)) if period else None
    details["period_to"] = _parse_period_date(period.group(2)) if period else None

    for field, pattern in BALANCE_RE.items():
        match = pattern.search(text)  # closing balance is at the end -> search everything
        if match:
            value, marker = parse_amount(match.group(1))
            details[field] = -value if marker == "DR" else value
        else:
            details[field] = None
    return details
