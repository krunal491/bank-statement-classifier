"""
Step 4 of the pipeline: check the extracted data for mistakes.

The most powerful check is the BALANCE CHECK:
    previous balance - debit + credit  must equal  this row's balance.
If it doesn't, either a row was read wrongly (e.g. OCR error) or a row is
missing. We flag those rows so the user can look at them.
"""

TOLERANCE = 0.01  # rupees


def check_balances(transactions, opening_balance=None):
    """
    Add a "balance_ok" field (True / False / None) to every transaction.
    Returns a list of human-readable problems.
    """
    problems = []
    previous = opening_balance
    for i, txn in enumerate(transactions, start=1):
        txn["balance_ok"] = None
        if txn.get("balance") is None:
            problems.append(f"Row {i}: balance is missing.")
        elif previous is not None:
            expected = round(previous - (txn.get("debit") or 0) + (txn.get("credit") or 0), 2)
            txn["balance_ok"] = abs(expected - txn["balance"]) <= TOLERANCE
            if not txn["balance_ok"] and _next_row_agrees(transactions, i, expected):
                # Only this balance looks wrong (e.g. OCR read 3 as 6), because the
                # NEXT row continues correctly from the expected value. Fix it.
                problems.append(
                    f"Row {i} ({txn['date']}): balance {txn['balance']:,.2f} looked misread; "
                    f"auto-corrected to {expected:,.2f}."
                )
                txn["balance_corrected_from"] = txn["balance"]
                txn["balance"] = expected
                txn["balance_ok"] = True
            elif not txn["balance_ok"]:
                problems.append(
                    f"Row {i} ({txn['date']}): expected balance {expected:,.2f} "
                    f"but statement shows {txn['balance']:,.2f}."
                )
        if txn.get("balance") is not None:
            previous = txn["balance"]
    return problems


def _next_row_agrees(transactions, row_number, expected):
    """True if the row after `row_number` (1-based) is consistent with `expected`."""
    if row_number >= len(transactions):
        return False
    nxt = transactions[row_number]
    if nxt.get("balance") is None:
        return False
    next_expected = round(expected - (nxt.get("debit") or 0) + (nxt.get("credit") or 0), 2)
    return abs(next_expected - nxt["balance"]) <= TOLERANCE


def find_duplicates(transactions):
    """Mark rows that appear twice (same date, description, amounts and balance)."""
    seen = set()
    problems = []
    for i, txn in enumerate(transactions, start=1):
        key = (txn["date"], txn["description"], txn.get("debit"), txn.get("credit"), txn.get("balance"))
        txn["is_duplicate"] = key in seen
        if txn["is_duplicate"]:
            problems.append(f"Row {i}: duplicate of an earlier row.")
        seen.add(key)
    return problems


def check_rows(transactions, period_from=None, period_to=None):
    """Simple sanity checks on each row."""
    problems = []
    previous_date = None
    for i, txn in enumerate(transactions, start=1):
        if txn.get("debit") is None and txn.get("credit") is None:
            problems.append(f"Row {i}: no debit or credit amount found.")
        if not txn.get("description"):
            problems.append(f"Row {i}: empty description.")
        day = txn.get("date")
        if day and previous_date and day < previous_date:
            problems.append(f"Row {i}: date {day} is earlier than the row before it.")
        if day and period_from and period_to and not (period_from <= day <= period_to):
            problems.append(f"Row {i}: date {day} is outside the statement period.")
        previous_date = day or previous_date
    return problems


def validate(transactions, account):
    """Run every check and return a summary report."""
    opening = account.get("opening_balance")
    # If the statement has no opening balance, work it out from the first row.
    if opening is None and transactions and transactions[0].get("balance") is not None:
        first = transactions[0]
        opening = round(first["balance"] + (first.get("debit") or 0) - (first.get("credit") or 0), 2)
        account["opening_balance_estimated"] = True
    problems = []
    problems += check_balances(transactions, opening)
    problems += find_duplicates(transactions)
    problems += check_rows(transactions, account.get("period_from"), account.get("period_to"))

    total_debit = round(sum(t.get("debit") or 0 for t in transactions), 2)
    total_credit = round(sum(t.get("credit") or 0 for t in transactions), 2)
    last_balance = next((t["balance"] for t in reversed(transactions) if t.get("balance") is not None), None)
    closing = account.get("closing_balance")
    if closing is not None and last_balance is not None and abs(closing - last_balance) > TOLERANCE:
        problems.append(f"Closing balance {closing:,.2f} does not match last row balance {last_balance:,.2f}.")

    checked = [t for t in transactions if t.get("balance_ok") is not None]
    accuracy = round(100 * sum(t["balance_ok"] for t in checked) / len(checked), 1) if checked else None
    return {
        "opening_balance": opening,
        "closing_balance": closing if closing is not None else last_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "transaction_count": len(transactions),
        "balance_check_pass_rate": accuracy,
        "problems": problems,
    }
