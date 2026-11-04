"""
Extra analysis on the classified transactions (all with pandas):

- category_summary : how much money went to each category
- monthly_summary  : money in / money out per month
- top_merchants    : where the most money was spent
- find_recurring   : payments that repeat every month (salary, rent, EMI, subscriptions)
"""

import pandas as pd


def category_summary(df):
    out = (
        df.assign(debit=df["debit"].fillna(0), credit=df["credit"].fillna(0))
        .groupby("category")
        .agg(transactions=("category", "size"), money_out=("debit", "sum"), money_in=("credit", "sum"))
        .reset_index()
        .sort_values("money_out", ascending=False)
    )
    total_out = out["money_out"].sum() or 1
    out["share_of_spending_%"] = (100 * out["money_out"] / total_out).round(1)
    return out


def monthly_summary(df):
    month = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    out = (
        df.assign(month=month, debit=df["debit"].fillna(0), credit=df["credit"].fillna(0))
        .groupby("month")
        .agg(money_in=("credit", "sum"), money_out=("debit", "sum"), transactions=("month", "size"))
        .reset_index()
    )
    out["net_savings"] = (out["money_in"] - out["money_out"]).round(2)
    return out


def top_merchants(df, limit=10):
    spends = df[df["debit"].notna() & (df["counterparty"] != "")]
    return (
        spends.groupby("counterparty")
        .agg(times=("debit", "size"), total_spent=("debit", "sum"), category=("category", "first"))
        .reset_index()
        .sort_values("total_spent", ascending=False)
        .head(limit)
    )


def find_recurring(df, min_months=2, amount_tolerance=0.10):
    """
    A payment is "recurring" when the same counterparty + category shows up
    in at least `min_months` different months with roughly the same amount
    (within 10%).
    """
    if df.empty:
        return pd.DataFrame(columns=["counterparty", "category", "type", "typical_amount", "months_seen", "frequency"])
    data = df.copy()
    data["amount"] = data["debit"].fillna(data["credit"])
    data["type"] = data["debit"].notna().map({True: "Money out", False: "Money in"})
    data["month"] = pd.to_datetime(data["date"]).dt.to_period("M")
    data["who"] = data["counterparty"].where(data["counterparty"] != "", data["description"].str[:25])

    rows = []
    for (who, category, kind), group in data.groupby(["who", "category", "type"]):
        months = group["month"].nunique()
        if months < min_months:
            continue
        typical = group["amount"].median()
        similar = (group["amount"] - typical).abs() <= amount_tolerance * typical
        if similar.sum() >= min_months:
            rows.append({
                "counterparty": who, "category": category, "type": kind,
                "typical_amount": round(typical, 2), "months_seen": months,
                "frequency": "Monthly" if months >= group.shape[0] * 0.8 else "Several times a month",
            })
    return pd.DataFrame(rows).sort_values("typical_amount", ascending=False) if rows else pd.DataFrame(
        columns=["counterparty", "category", "type", "typical_amount", "months_seen", "frequency"])


def mark_recurring(df, recurring):
    """Add an is_recurring column to the transactions."""
    keys = set(zip(recurring.get("counterparty", []), recurring.get("category", [])))
    who = df["counterparty"].where(df["counterparty"] != "", df["description"].str[:25])
    df["is_recurring"] = [(w, c) in keys for w, c in zip(who, df["category"])]
    return df
