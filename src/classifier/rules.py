"""
Classifier part 1: hand-written RULES (keywords).

Each category has a list of keywords. If a description contains one of them,
we use that category. Rules are fast, easy to explain and very accurate for
well-known merchants, but they can't handle names they've never seen - that is
what the machine learning model (ml_model.py) is for.

Order matters: the first matching rule wins, so specific rules come first
(e.g. "REFUND AMAZON" must be a refund, not shopping).
"""

import re

# (category, keywords, only_for) - only_for can be "debit", "credit" or None (both)
RULES = [
    ("Refunds & Cashback", ["REFUND", "CASHBACK", "REVERSAL", "REVERSED", "CHARGEBACK"], "credit"),
    ("Salary", ["SALARY", r"\bSAL\b", "PAYROLL", "STIPEND"], "credit"),
    ("Interest", ["INTEREST", r"INT\.PD", r"\bINT CREDIT\b", r"\bSB INT\b"], "credit"),
    ("Bank Charges", ["CHARGES", "CHARGE", "ANNUAL FEE", "PROCESSING FEE", "GST ON", "MIN BAL", "PENALTY"], "debit"),
    ("ATM Withdrawal", [r"\bATM\b", r"\bNWD\b", "CASH WITHDRAWAL", r"ATM-WDL", "CASH WDL"], "debit"),
    ("Taxes", ["INCOME TAX", "CBDT", "TDS", "GST PAYMENT", "PROPERTY TAX", "ADVANCE TAX", "CHALLAN"], "debit"),
    ("Insurance", ["INSURANCE", r"\bLIC\b", "LOMBARD", "POLICYBAZAAR", "HDFC LIFE", "MAX LIFE", "STAR HEALTH"], None),
    ("Investments", ["ZERODHA", "GROWW", "UPSTOX", "MUTUAL FUND", r"\bSIP\b", r"\bMF\b", r"\bPPF\b", r"\bNPS\b", "DEMAT", "BROKING"], None),
    ("EMI & Loans", [r"\bEMI\b", "LOAN", "NACH", r"\bACH D", "BAJAJ FIN", "TATA CAPITAL"], "debit"),
    ("Rent", [r"\bRENT\b", "HOUSE RENT", "NOBROKER"], "debit"),
    ("Food & Dining", ["SWIGGY", "ZOMATO", "DOMINOS", "PIZZA", "MCDONALD", "STARBUCKS", r"\bKFC\b", "RESTAURANT", "CAFE", "BIRYANI", "BURGER"], None),
    ("Groceries", ["BIGBASKET", "BLINKIT", "ZEPTO", "DMART", "GROFERS", "JIOMART", "SUPERMARKET", "KIRANA", "RELIANCE FRESH"], None),
    ("Transport & Fuel", ["UBER", r"\bOLA", "RAPIDO", "PETROL", "FUEL", "IOCL", "HPCL", "BPCL", "INDIAN OIL", "FASTAG", "METRO"], None),
    ("Travel", ["IRCTC", "MAKEMYTRIP", "GOIBIBO", "INDIGO", "AIR INDIA", "REDBUS", "OYO", "CLEARTRIP", "HOTEL", "AIRLINES"], None),
    ("Bills & Utilities", ["ELECTRICITY", "BESCOM", "AIRTEL", r"\bJIO\b", "RECHARGE", "BROADBAND", "FIBERNET", "DTH", "WATER BILL", r"\bGAS\b", "POSTPAID", "TATA PLAY", "POWER"], None),
    ("Entertainment & Subscriptions", ["NETFLIX", "SPOTIFY", "HOTSTAR", "PRIME", "BOOKMYSHOW", "PVR", "INOX", "YOUTUBE", "STEAM"], None),
    ("Healthcare", ["PHARMACY", "PHARMEASY", "HOSPITAL", "APOLLO", r"\b1MG\b", "MEDPLUS", "CLINIC", "PATHLAB", "PRACTO", "MEDICAL"], None),
    ("Education", ["BYJUS", "UNACADEMY", "COURSERA", "UDEMY", "SCHOOL", "COLLEGE", "UNIVERSITY", "TUITION", "UPGRAD", r"\bFEES?\b"], None),
    ("Shopping", ["AMAZON", "FLIPKART", "MYNTRA", "AJIO", "NYKAA", "CROMA", "DECATHLON", "MEESHO", "LIFESTYLE", "IKEA", "WESTSIDE", "RELIANCE DIGITAL"], None),
    ("Transfers", [r"SELF TRANSFER", r"IMPS/P2A", r"\bP2A\b", r"TO TRANSFER", r"FUND TRANSFER"], None),
]

# Pre-compile all patterns once.
COMPILED_RULES = [
    (category, re.compile("|".join(keywords), re.IGNORECASE), only_for)
    for category, keywords, only_for in RULES
]


def classify_by_rules(description, direction=None):
    """
    Return (category, matched_keyword) or (None, None) if no rule matches.
    `direction` is "debit" or "credit"; some rules only apply to one of them.
    """
    for category, pattern, only_for in COMPILED_RULES:
        if only_for and direction and only_for != direction:
            continue
        match = pattern.search(description or "")
        if match:
            return category, match.group(0)
    return None, None
