"""
Step 3 of the pipeline: find the transactions in the lines of text.

The idea is simple and works for many bank layouts:

1. Find the TABLE HEADER line (it contains words like "Debit", "Credit",
   "Withdrawal", "Deposit", "Balance"). Remember where each money column
   sits horizontally on the page.
2. Every line that STARTS WITH A DATE begins a new transaction.
3. A line without a date and without amounts is the next line of the
   previous transaction's description (long descriptions wrap).
4. Money values on a line are put into the Debit / Credit / Balance
   column whose header is closest to them.
5. If we still can't tell debit from credit (e.g. one "Amount" column),
   we look at how the balance changed: balance went down = debit.
"""

import re

from src.layout import group_into_lines
from src.utils import clean_text, is_amount, parse_amount, parse_date

DEBIT_WORDS = {"debit", "debits", "withdrawal", "withdrawals", "withdrawl", "paid"}
CREDIT_WORDS = {"credit", "credits", "deposit", "deposits", "received"}
BALANCE_WORDS = {"balance", "bal"}
AMOUNT_WORDS = {"amount", "amt", "amt."}

# Lines that are not transactions even though they may contain numbers.
SKIP_PATTERNS = re.compile(
    r"opening balance|closing balance|^page\s*\d|page \d+ of|statement summary|"
    r"computer generated|carried forward|brought forward|^total|grand total|"
    r"does not require|end of statement|\bb/f\b|\bc/f\b",
    re.IGNORECASE,
)

# Words that suggest money came IN (used only as a last resort).
CREDIT_HINTS = re.compile(
    r"\bCR\b|/CR/|CREDIT|SALARY|\bSAL\b|REFUND|CASHBACK|REVERSAL|INTEREST|INT\.PD|"
    r"DEPOSIT|BY TRANSFER|BY CLG|RECEIVED",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Header detection
# ---------------------------------------------------------------------------
def _word_key(text):
    return text.lower().strip(".:()/[]")


def find_columns(line):
    """
    If this line is a table header, return the horizontal centre of each
    money column, e.g. {"debit": 420.5, "credit": 480.0, "balance": 545.2}.
    Otherwise return None.
    """
    words = line["words"]
    keys = [_word_key(w["text"]) for w in words]
    has_balance = any(k in BALANCE_WORDS for k in keys)
    has_money_col = any(k in DEBIT_WORDS | CREDIT_WORDS | AMOUNT_WORDS for k in keys)
    if not (has_balance and has_money_col):
        return None

    def column_for(key):
        if key in DEBIT_WORDS:
            return "debit"
        if key in CREDIT_WORDS:
            return "credit"
        if key in BALANCE_WORDS:
            return "balance"
        if key in AMOUNT_WORDS:
            return "amount"
        return None

    columns = {}
    # Remember if there is a "Value Date" column (needed to tell a value date
    # apart from a date that is part of the description).
    for i, key in enumerate(keys):
        if key in ("value", "valuedt") or (key == "dt" and i > 0 and keys[i - 1] == "value"):
            columns["value_date"] = words[i]["x0"]
    i = 0
    while i < len(words):
        name = column_for(keys[i])
        if name is None:
            i += 1
            continue
        # A header can be several words ("Withdrawal Amount (INR)").
        # Take the whole phrase so we get its real centre.
        start, end = words[i]["x0"], words[i]["x1"]
        # "Withdrawal Amt." is still the withdrawal (debit) column.
        j = i + 1
        while j < len(words) and column_for(keys[j]) in (None, "amount") and words[j]["x0"] - end < 12:
            end = words[j]["x1"]
            j += 1
        if name not in columns:
            columns[name] = (start + end) / 2
        i = j

    # If there are real debit/credit columns, "amount" is just part of their name.
    if "debit" in columns or "credit" in columns:
        columns.pop("amount", None)
    return columns


# ---------------------------------------------------------------------------
# Row parsing
# ---------------------------------------------------------------------------
def _leading_date(tokens):
    """
    Look for a date at the start of the line.
    Handles "01/04/2024" (one token) and "01 Apr 2024" (three tokens).
    Also skips a serial number in front ("1  01/04/2024 ...").
    Returns (date, number_of_tokens_used) or (None, 0).
    """
    starts = [0]
    if tokens and tokens[0].isdigit() and len(tokens[0]) <= 4:
        starts.append(1)  # maybe a serial number
    for start in starts:
        for size in (1, 3, 2):
            if len(tokens) >= start + size:
                parsed = parse_date(" ".join(tokens[start:start + size]))
                if parsed:
                    return parsed, start + size
    return None, 0


def _amount_tokens(words):
    """
    Find money values on a line. A separate "Cr"/"Dr" word right after an
    amount is attached to it.
    Returns list of dicts: {"value", "marker", "x", "index"}.
    """
    found = []
    for i, word in enumerate(words):
        text = word["text"]
        if not is_amount(text):
            continue
        value, marker = parse_amount(text)
        if value is None:
            continue
        if marker is None and i + 1 < len(words):
            nxt = words[i + 1]["text"].upper().strip(".()")
            if nxt in ("CR", "DR"):
                marker = nxt
        found.append({"value": value, "marker": marker, "x": (word["x0"] + word["x1"]) / 2, "index": i})
    return found


def _nearest_column(x, columns, allowed):
    options = {k: v for k, v in columns.items() if k in allowed}
    if not options:
        return None
    return min(options, key=lambda k: abs(options[k] - x))


def parse_row(line, columns, row_date=None, date_tokens=0):
    """Turn one table line into a transaction dict."""
    words = line["words"]
    tokens = [w["text"] for w in words]
    amounts = _amount_tokens(words)

    txn = {
        "date": row_date, "value_date": None, "description": "", "ref_no": "",
        "debit": None, "credit": None, "balance": None, "direction": None, "amount": None,
    }

    # --- money columns ---------------------------------------------------
    if amounts:
        has_balance_col = columns is None or "balance" in columns
        money_columns = {"debit", "credit", "balance", "amount"}
        if has_balance_col and (len(amounts) >= 2 or (columns and
                _nearest_column(amounts[-1]["x"], columns, money_columns) == "balance")):
            bal = amounts.pop()
            txn["balance"] = -bal["value"] if bal["marker"] == "DR" else bal["value"]
        if amounts:
            amt = amounts[0]
            txn["amount"] = abs(amt["value"])
            if amt["marker"] == "DR":
                txn["direction"] = "debit"
            elif amt["marker"] == "CR":
                txn["direction"] = "credit"
            elif columns:
                column = _nearest_column(amt["x"], columns, {"debit", "credit", "amount"})
                if column in ("debit", "credit"):
                    txn["direction"] = column
            if amt["value"] < 0 and txn["direction"] is None:
                txn["direction"] = "debit"

    # --- text part (description, value date, reference number) -------------
    first_amount_index = min([a["index"] for a in _amount_tokens(words)] or [len(tokens)])
    text_tokens = tokens[date_tokens:first_amount_index]

    # Value date right after the transaction date (SBI, ICICI style)
    for size in (1, 3):
        if len(text_tokens) >= size and parse_date(" ".join(text_tokens[:size])):
            txn["value_date"] = parse_date(" ".join(text_tokens[:size]))
            text_tokens = text_tokens[size:]
            break
    # ... or value date just before the amounts (HDFC style)
    has_value_col = columns is not None and "value_date" in columns
    if txn["value_date"] is None and has_value_col and text_tokens and parse_date(text_tokens[-1]):
        txn["value_date"] = parse_date(text_tokens[-1])
        text_tokens = text_tokens[:-1]
    # A standalone long number at the start or end of the text is the cheque/ref number.
    if text_tokens and re.fullmatch(r"\d{5,}", text_tokens[-1]):
        txn["ref_no"] = text_tokens.pop()
    elif text_tokens and re.fullmatch(r"\d{5,}", text_tokens[0]):
        txn["ref_no"] = text_tokens.pop(0)

    txn["description"] = clean_text(" ".join(text_tokens))
    return txn


def _join_description(previous, extra):
    """Join wrapped description lines. No space after '/', '-' or '*'."""
    if not previous:
        return extra
    if previous.endswith(("/", "-", "*")):
        return previous + extra
    return previous + " " + extra


def _merge_split_numbers(words):
    """
    OCR sometimes splits one number into two words: "1,29," + "704.46".
    Join them back together when they are next to each other.
    """
    merged = []
    for word in sorted(words, key=lambda w: w["x0"]):
        previous = merged[-1]["text"] if merged else ""
        unfinished = re.fullmatch(r"[\d,.]*\d,?", previous) and not re.search(r"\.\d{2}$", previous)
        continues = re.match(r",?\d", word["text"]) and (previous.endswith(",") or word["text"].startswith(","))
        if merged and unfinished and continues and word["x0"] - merged[-1]["x1"] < 8:
            last = merged[-1]
            merged[-1] = {**last, "text": last["text"] + word["text"], "x1": word["x1"]}
        else:
            merged.append(word)
    return merged


def _fix_ocr_token(text):
    """Fix common OCR mistakes in numbers: 'O'->'0', '1.18,576.21' -> '118576.21'."""
    if parse_date(text):
        return text
    candidate = text
    if re.search(r"\d", text):
        # letters that OCR often confuses with digits
        for wrong, right in (("O", "0"), ("o", "0"), ("§", "5"), ("$", "5"), ("l", "1"), ("I", "1")):
            candidate = candidate.replace(wrong, right)
    match = re.fullmatch(r"(\(?-?)([\d.,]+)[.,](\d{2})(\)?)((?:Cr|Dr|CR|DR)?)", candidate)
    if match and len(match.group(2).replace(",", "").replace(".", "")) >= 1:
        whole = re.sub(r"[.,]", "", match.group(2))
        return f"{match.group(1)}{whole}.{match.group(3)}{match.group(4)}{match.group(5)}"
    return text


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def extract_transactions(pages, opening_balance=None):
    """
    Find all transactions in all pages.

    `pages` comes from pdf_reader.read_pdf(). Returns a list of dicts with
    date, value_date, description, ref_no, debit, credit, balance, page.
    """
    transactions = []
    columns = None          # remembered across pages (headers are not always repeated)
    current = None          # the transaction we are building
    in_table = False

    for page in pages:
        lines = group_into_lines(page["words"])
        if page["type"] == "image":
            for line in lines:
                # first glue split numbers together, then fix misread characters
                merged = _merge_split_numbers(line["words"])
                line["words"] = [{**w, "text": _fix_ocr_token(w["text"])} for w in merged]
                line["text"] = " ".join(w["text"] for w in line["words"])

        for line in lines:
            header = find_columns(line)
            if header:
                columns, in_table = header, True
                current = None
                continue
            text = line["text"]
            if SKIP_PATTERNS.search(text):
                current = None
                continue

            tokens = [w["text"] for w in line["words"]]
            row_date, used = _leading_date(tokens)
            has_amounts = bool(_amount_tokens(line["words"]))

            if row_date and has_amounts:
                # A normal transaction row.
                txn = parse_row(line, columns, row_date, used)
                txn["page"] = page["number"]
                transactions.append(txn)
                current, in_table = txn, True
            elif not row_date and has_amounts and in_table and current is not None:
                # Edge case: some banks print the date only once per day.
                txn = parse_row(line, columns, current["date"], 0)
                if txn["description"]:
                    txn["page"] = page["number"]
                    transactions.append(txn)
                    current = txn
            elif not has_amounts and current is not None and in_table:
                # Edge case: the description continues on the next line.
                extra = clean_text(text if not row_date else " ".join(tokens[used:]))
                if extra and len(extra) < 120:
                    current["description"] = _join_description(current["description"], extra)

    _resolve_directions(transactions, opening_balance)
    for txn in transactions:
        txn["debit"] = txn["amount"] if txn["direction"] == "debit" else None
        txn["credit"] = txn["amount"] if txn["direction"] == "credit" else None
    return transactions


def fix_dates(transactions, period_from=None, period_to=None):
    """
    Edge case for OCR: a misread digit can turn 16/05 into 16/08.
    If a row's date is outside the statement period (or jumps backwards)
    but its value date looks right, use the value date instead.
    """
    previous = None
    for txn in transactions:
        day, value_day = txn["date"], txn.get("value_date")
        bad = (period_from and period_to and day and not (period_from <= day <= period_to)) or (
            previous and day and day < previous)
        if bad and value_day and (not period_from or period_from <= value_day <= period_to) and (
                not previous or value_day >= previous):
            txn["date"], txn["value_date"] = value_day, day
        previous = txn["date"] or previous
    return transactions


def _resolve_directions(transactions, opening_balance):
    """
    Work out debit/credit for rows where the column didn't tell us,
    using the change in balance. Falls back to keywords.
    """
    previous = opening_balance
    for txn in transactions:
        amount, balance = txn["amount"], txn["balance"]
        if txn["direction"] is None and amount is not None:
            if previous is not None and balance is not None:
                change = round(balance - previous, 2)
                if abs(abs(change) - amount) < 0.011:
                    txn["direction"] = "credit" if change > 0 else "debit"
            if txn["direction"] is None:
                txn["direction"] = "credit" if CREDIT_HINTS.search(txn["description"]) else "debit"
        if balance is not None:
            previous = balance
