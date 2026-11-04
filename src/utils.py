"""
Small helper functions used everywhere in the project.

- parse_date():   turns "01/04/2024", "01-Apr-2024", "1 Apr 24" ... into a date
- parse_amount(): turns "1,23,456.78", "500.00 Cr", "(250.00)" ... into a number
- is_amount():    tells whether a piece of text looks like a money amount
"""

import re
from datetime import date, datetime

# All date formats we know about. Indian banks write the day first.
DATE_FORMATS = [
    "%d/%m/%Y", "%d/%m/%y",
    "%d-%m-%Y", "%d-%m-%y",
    "%d.%m.%Y", "%d.%m.%y",
    "%d-%b-%Y", "%d-%b-%y",
    "%d %b %Y", "%d %b %y",
    "%d/%b/%Y", "%d/%b/%y",
    "%d-%B-%Y", "%d %B %Y",
    "%Y-%m-%d", "%Y/%m/%d",
]

# A money amount must have exactly two digits after the decimal point.
# This stops us from mistaking reference numbers (e.g. 412345678901) for money.
# Examples it matches: 500.00   1,234.50   1,23,456.78   -20.00   500.00Cr
AMOUNT_PATTERN = re.compile(
    r"^\(?-?(?:₹|Rs\.?|INR)?\s?\d{1,3}(?:,\d{2,3})*(?:\.\d{2})\)?(?:\s?(?:Cr|Dr|CR|DR|cr|dr)\.?)?$"
    r"|^\(?-?(?:₹|Rs\.?|INR)?\s?\d+\.\d{2}\)?(?:\s?(?:Cr|Dr|CR|DR|cr|dr)\.?)?$"
)


def parse_date(text):
    """Return a `date` if `text` is a date in any known format, otherwise None."""
    if not text:
        return None
    cleaned = text.strip().strip(",.;:|").replace("  ", " ")
    # OCR sometimes reads "Apr" as "APR" or "apr" - normalise the case.
    cleaned = re.sub(r"[A-Za-z]{3,9}", lambda m: m.group(0).capitalize(), cleaned)
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
        # Ignore silly years that come from OCR mistakes.
        if 1990 <= parsed.year <= date.today().year + 1:
            return parsed
    return None


def is_amount(text):
    """True if the text looks like a money amount such as '1,234.50' or '200.00 Cr'."""
    return bool(text) and bool(AMOUNT_PATTERN.match(text.strip()))


def parse_amount(text):
    """
    Convert a money string to a float.

    Returns (value, marker) where marker is "CR", "DR" or None.
    "(250.00)" and "-250.00" are treated as negative numbers.
    """
    if text is None:
        return None, None
    raw = text.strip()
    marker = None
    match = re.search(r"(Cr|Dr|CR|DR|cr|dr)\.?$", raw)
    if match:
        marker = match.group(1).upper()
        raw = raw[: match.start()].strip()

    negative = raw.startswith("-") or (raw.startswith("(") and raw.endswith(")"))
    digits = re.sub(r"[^\d.]", "", raw)
    if not digits:
        return None, marker
    try:
        value = float(digits)
    except ValueError:
        return None, marker
    return (-value if negative else value), marker


def clean_text(text):
    """Collapse repeated spaces and strip the ends."""
    return re.sub(r"\s+", " ", text or "").strip()
