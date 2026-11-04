"""
Fake (synthetic) transaction data.

Real bank statements contain private data, so we generate realistic fake
ones instead. This file is used by:
  - generate_samples.py        -> sample PDF statements
  - generate_training_data.py  -> labelled data for the ML classifier
"""

import random

from src.classifier.categories import ALL_CATEGORIES  # noqa: F401  (re-exported)

# Merchants per category: (display name, UPI handle).
MERCHANTS = {
    "Food & Dining": [
        ("SWIGGY", "swiggy@ybl"), ("ZOMATO", "zomato@hdfcbank"), ("DOMINOS PIZZA", "dominos@icici"),
        ("MCDONALDS", "mcd@paytm"), ("STARBUCKS", "starbucks@axisbank"), ("KFC", "kfc@ybl"),
        ("HALDIRAMS", "haldirams@paytm"), ("CHAAYOS CAFE", "chaayos@okicici"),
        ("BURGER KING", "bk@ybl"), ("SHREE SAGAR RESTAURANT", "sagar@okaxis"),
        ("THIRD WAVE COFFEE", "twc@ybl"), ("BEHROUZ BIRYANI", "behrouz@paytm"),
    ],
    "Groceries": [
        ("BIGBASKET", "bigbasket@icici"), ("BLINKIT", "blinkit@hdfcbank"), ("ZEPTO", "zepto@ybl"),
        ("DMART", "dmart@axisbank"), ("RELIANCE FRESH", "relfresh@ybl"), ("MORE SUPERMARKET", "more@paytm"),
        ("JIOMART", "jiomart@ybl"), ("SPENCERS RETAIL", "spencers@icici"), ("NATURES BASKET", "nb@ybl"),
        ("SHARMA KIRANA STORE", "sharmakirana@okhdfcbank"),
    ],
    "Shopping": [
        ("AMAZON", "amazon@apl"), ("FLIPKART", "flipkart@axisbank"), ("MYNTRA", "myntra@ybl"),
        ("AJIO", "ajio@ybl"), ("NYKAA", "nykaa@icici"), ("CROMA", "croma@hdfcbank"),
        ("DECATHLON", "decathlon@ybl"), ("LIFESTYLE STORES", "lifestyle@paytm"), ("MEESHO", "meesho@ybl"),
        ("RELIANCE DIGITAL", "reldigital@ybl"), ("IKEA INDIA", "ikea@icici"), ("WESTSIDE", "westside@ybl"),
    ],
    "Transport & Fuel": [
        ("UBER INDIA", "uber@axisbank"), ("OLA CABS", "olacabs@ybl"), ("RAPIDO", "rapido@ybl"),
        ("INDIAN OIL PETROL PUMP", "iocl@icici"), ("HP PETROL PUMP", "hpcl@ybl"),
        ("BHARAT PETROLEUM", "bpcl@hdfcbank"), ("FASTAG RECHARGE", "fastag@icici"),
        ("NAMMA METRO", "bmrcl@ybl"), ("SHELL FUEL STATION", "shell@ybl"),
    ],
    "Travel": [
        ("IRCTC", "irctc@sbi"), ("MAKEMYTRIP", "mmt@icici"), ("INDIGO AIRLINES", "indigo@hdfcbank"),
        ("GOIBIBO", "goibibo@ybl"), ("REDBUS", "redbus@ybl"), ("OYO ROOMS", "oyo@paytm"),
        ("AIR INDIA", "airindia@icici"), ("CLEARTRIP", "cleartrip@axisbank"), ("TAJ HOTELS", "taj@hdfcbank"),
    ],
    "Bills & Utilities": [
        ("BESCOM ELECTRICITY", "bescom@ybl"), ("AIRTEL POSTPAID", "airtel@airtel"),
        ("JIO RECHARGE", "jio@ybl"), ("VI MOBILE RECHARGE", "vi@paytm"), ("ACT FIBERNET", "actfibernet@icici"),
        ("TATA PLAY DTH", "tataplay@ybl"), ("MAHANAGAR GAS", "mgl@hdfcbank"), ("BWSSB WATER BILL", "bwssb@ybl"),
        ("INDANE GAS BOOKING", "indane@ybl"), ("TORRENT POWER", "torrent@icici"),
    ],
    "Entertainment & Subscriptions": [
        ("NETFLIX", "netflix@hdfcbank"), ("SPOTIFY", "spotify@icici"), ("BOOKMYSHOW", "bms@ybl"),
        ("PVR CINEMAS", "pvr@axisbank"), ("HOTSTAR", "hotstar@ybl"), ("AMAZON PRIME", "prime@apl"),
        ("YOUTUBE PREMIUM", "youtube@okicici"), ("INOX MOVIES", "inox@ybl"), ("STEAM GAMES", "steam@icici"),
    ],
    "Healthcare": [
        ("APOLLO PHARMACY", "apollo@ybl"), ("PHARMEASY", "pharmeasy@icici"), ("1MG HEALTH", "1mg@ybl"),
        ("MANIPAL HOSPITAL", "manipal@hdfcbank"), ("FORTIS HEALTHCARE", "fortis@icici"),
        ("MEDPLUS", "medplus@ybl"), ("PRACTO", "practo@paytm"), ("DR LAL PATHLABS", "lalpath@ybl"),
        ("CITY DENTAL CLINIC", "dental@okaxis"),
    ],
    "Education": [
        ("BYJUS", "byjus@icici"), ("UNACADEMY", "unacademy@ybl"), ("COURSERA", "coursera@hdfcbank"),
        ("UDEMY", "udemy@icici"), ("DPS SCHOOL FEES", "dps@sbi"), ("VIT UNIVERSITY FEE", "vit@sbi"),
        ("SAPNA BOOK HOUSE", "sapna@ybl"), ("UPGRAD EDUCATION", "upgrad@ybl"),
    ],
    "Investments": [
        ("ZERODHA BROKING", "zerodha@hdfcbank"), ("GROWW MUTUAL FUND SIP", "groww@ybl"),
        ("UPSTOX", "upstox@icici"), ("ICICI PRU MF SIP", "icicipru@icici"), ("COIN BY ZERODHA", "coin@hdfcbank"),
        ("PPF DEPOSIT", None), ("SBI MUTUAL FUND", "sbimf@sbi"), ("NPS CONTRIBUTION", None),
    ],
    "Insurance": [
        ("LIC PREMIUM", "lic@sbi"), ("HDFC LIFE INSURANCE", "hdfclife@hdfcbank"),
        ("STAR HEALTH INSURANCE", "starhealth@icici"), ("ICICI LOMBARD", "lombard@icici"),
        ("POLICYBAZAAR", "policybazaar@ybl"), ("MAX LIFE INSURANCE", "maxlife@axisbank"),
    ],
}

PEOPLE = [
    "RAHUL KUMAR", "PRIYA SINGH", "AMIT PATEL", "SNEHA REDDY", "VIKRAM NAIR", "ANJALI MEHTA",
    "ROHIT VERMA", "KAVYA IYER", "ARJUN DAS", "POOJA JOSHI", "SURESH BABU", "NEHA GUPTA",
]
EMPLOYERS = ["ACME TECHNOLOGIES PVT LTD", "INFOSYS LIMITED", "TATA CONSULTANCY SERVICES", "WIPRO LTD"]
LENDERS = ["BAJAJ FINANCE LTD", "HDFC BANK LOAN", "ICICI HOME LOAN", "TATA CAPITAL", "AXIS BANK CAR LOAN"]
UPI_BANKS = ["YESB", "HDFC", "ICIC", "UTIB", "SBIN", "PYTM"]


def ref_number(rng, digits=12):
    return "".join(rng.choice("0123456789") for _ in range(digits))


def upi_description(rng, bank, name, handle, direction="DR"):
    """Write a UPI narration the way each bank prints it."""
    ref = ref_number(rng)
    handle = handle or (name.split()[0].lower() + "@okaxis")
    upi_bank = rng.choice(UPI_BANKS)
    if bank == "HDFC":
        return f"UPI-{name}-{handle.upper()}-{upi_bank}0000001-{ref}-PAYMENT"
    if bank == "ICICI":
        return f"UPI/{ref}/Payment/{handle}/{upi_bank}"
    if bank == "AXIS":
        return f"UPI/P2M/{ref}/{name}/{upi_bank}"
    if bank == "KOTAK":
        return f"UPI/{name}/{ref}/UPI Payment"
    return f"UPI/{direction}/{ref}/{name}/{upi_bank}/{handle}/Payment"


def card_description(rng, name):
    return rng.choice([
        f"POS {rng.randint(400000, 499999)}XXXXXX{rng.randint(1000, 9999)} {name}",
        f"DEBIT CARD PURCHASE {name} BANGALORE",
        f"ECOM PUR/{name}/{ref_number(rng, 8)}",
    ])


def make_transaction(rng, category, bank="SBI", month_name="APR"):
    """
    Create one fake transaction for a category.
    Returns (description, kind) where kind is "debit" or "credit".
    """
    if category == "Salary":
        employer = rng.choice(EMPLOYERS)
        return rng.choice([
            f"NEFT CR-{ref_number(rng, 4)}-{employer}-SALARY {month_name}",
            f"BY TRANSFER-NEFT*{employer}*SAL {month_name}",
            f"SALARY CREDIT {employer}",
        ]), "credit"
    if category == "Rent":
        person = rng.choice(PEOPLE)
        return rng.choice([
            f"IMPS/P2A/{ref_number(rng)}/{person}/HOUSE RENT",
            f"NEFT DR-{person}-RENT {month_name}",
            f"UPI/DR/{ref_number(rng)}/{person}/SBIN/rent@okaxis/Rent",
        ]), "debit"
    if category == "EMI & Loans":
        lender = rng.choice(LENDERS)
        return rng.choice([
            f"NACH DR {lender} EMI",
            f"ACH D- {lender}-{ref_number(rng, 8)}",
            f"EMI {ref_number(rng, 7)} {lender}",
            f"LOAN REPAYMENT {lender}",
        ]), "debit"
    if category == "ATM Withdrawal":
        return rng.choice([
            f"ATM WDL ATM CASH {rng.randint(1000, 9999)} MG ROAD BANGALORE",
            f"NWD-{rng.randint(400000, 499999)}XXXXXX{rng.randint(1000, 9999)}-ATM CASH",
            f"CASH WITHDRAWAL ATM ID {ref_number(rng, 6)}",
            f"ATM-WDL/{ref_number(rng, 6)}/KORAMANGALA",
        ]), "debit"
    if category == "Transfers":
        person = rng.choice(PEOPLE)
        direction = rng.choice(["DR", "CR"])
        kind = "debit" if direction == "DR" else "credit"
        return rng.choice([
            upi_description(rng, bank, person, None, direction),
            f"IMPS/P2A/{ref_number(rng)}/{person}",
            f"NEFT {direction}-{person}-SELF TRANSFER",
            f"TO TRANSFER-{person}",
        ]), kind
    if category == "Bank Charges":
        return rng.choice([
            "SMS ALERT CHARGES QTR", "DEBIT CARD ANNUAL FEE", "GST ON CHARGES",
            "MIN BAL CHARGES", "CHEQUE BOOK CHARGES", "ATM DECLINE CHARGE", "IMPS CHARGES INCL GST",
        ]), "debit"
    if category == "Interest":
        return rng.choice([
            "CREDIT INTEREST", "INT.PD:01-01-2024 TO 31-03-2024", "SB INTEREST CREDIT",
            "INTEREST ON FD", "INT CREDIT QUARTERLY",
        ]), "credit"
    if category == "Refunds & Cashback":
        merchant = rng.choice(["AMAZON", "FLIPKART", "PAYTM", "SWIGGY", "PHONEPE", "MYNTRA"])
        return rng.choice([
            f"REFUND {merchant} ORDER {ref_number(rng, 8)}",
            f"CASHBACK {merchant}",
            f"REVERSAL UPI {ref_number(rng)} {merchant}",
            f"UPI/CR/{ref_number(rng)}/{merchant}/YESB/refund@ybl/Refund",
        ]), "credit"
    if category == "Taxes":
        return rng.choice([
            "INCOME TAX PAYMENT CBDT", "GST PAYMENT CHALLAN", "PROPERTY TAX BBMP",
            f"TAX PAYMENT TDS CHALLAN {ref_number(rng, 6)}", "ADVANCE TAX ITNS 280",
        ]), "debit"

    # Categories that come from the merchant list.
    name, handle = rng.choice(MERCHANTS[category])
    style = rng.random()
    if style < 0.7:
        return upi_description(rng, bank, name, handle), "debit"
    if style < 0.9:
        return card_description(rng, name), "debit"
    return f"NEFT DR-{name}-{ref_number(rng, 6)}", "debit"
