"""
Create labelled training data for the ML classifier and measure its accuracy.

Run:  python -m scripts.generate_training_data

Writes data/training_data.csv (description, direction, category), trains the
model, prints accuracy on a held-out test set and saves the model.
"""

import random
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from scripts.synthetic import ALL_CATEGORIES, make_transaction
from src.classifier import ml_model

ROWS_PER_CATEGORY = 220
BANKS = ["SBI", "HDFC", "ICICI", "AXIS", "KOTAK"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def make_rows(seed):
    rng = random.Random(seed)
    rows = []
    for category in ALL_CATEGORIES:
        for _ in range(ROWS_PER_CATEGORY):
            desc, direction = make_transaction(rng, category, rng.choice(BANKS), rng.choice(MONTHS))
            rows.append({"description": desc, "direction": direction, "category": category})
    data = pd.DataFrame(rows)
    # Drop rows that are the same apart from numbers, so the test set is not
    # full of near-copies of the training set.
    data["_key"] = [ml_model.normalise(d, k) for d, k in zip(data.description, data.direction)]
    return data.drop_duplicates("_key").drop(columns="_key")


# Merchants that do NOT appear in the training data - checks that the model
# generalises instead of memorising names.
UNSEEN_EXAMPLES = [
    ("UPI/DR/412345678901/CAFE COFFEE DAY/YESB/ccd@ybl/Payment", "debit", "Food & Dining"),
    ("POS 412345XXXXXX1234 SUBWAY RESTAURANT", "debit", "Food & Dining"),
    ("UPI/DR/412345678901/WELLNESS PHARMACY/HDFC/wellness@okaxis/Payment", "debit", "Healthcare"),
    ("UPI/DR/412345678901/ESSAR PETROL PUMP/ICIC/essar@icici/Payment", "debit", "Transport & Fuel"),
    ("DEBIT CARD PURCHASE TANISHQ SHOPPING MALL BANGALORE", "debit", "Shopping"),
    ("UPI/DR/412345678901/NAMDHARI SUPERMARKET/YESB/nf@ybl/Payment", "debit", "Groceries"),
    ("NEFT DR-AAKASH INSTITUTE SCHOOL FEES-123456", "debit", "Education"),
    ("UPI/DR/412345678901/ZEE5 SUBSCRIPTION/YESB/zee5@ybl/Payment", "debit", "Entertainment & Subscriptions"),
    ("UPI/DR/412345678901/ADANI ELECTRICITY/YESB/adani@ybl/Payment", "debit", "Bills & Utilities"),
    ("UPI/DR/412345678901/VISTARA AIRLINES/ICIC/vistara@icici/Payment", "debit", "Travel"),
]


def main():
    data = make_rows(seed=2024)
    out = Path(ml_model.TRAINING_FILE)
    out.parent.mkdir(exist_ok=True)
    data.to_csv(out, index=False)
    print(f"Saved {len(data)} rows to {out}")

    # Honest evaluation: train on 80%, test on the other 20%.
    train_df, test_df = train_test_split(data, test_size=0.2, random_state=0, stratify=data["category"])
    model = ml_model.build_model()
    model.fit([ml_model.normalise(d, k) for d, k in zip(train_df.description, train_df.direction)],
              train_df.category)
    predicted = model.predict([ml_model.normalise(d, k) for d, k in zip(test_df.description, test_df.direction)])
    print(classification_report(test_df.category, predicted, digits=3))

    print("Merchants never seen in training:")
    hits = 0
    for desc, direction, expected in UNSEEN_EXAMPLES:
        got = model.predict([ml_model.normalise(desc, direction)])[0]
        hits += got == expected
        print(f"  {'OK ' if got == expected else 'X  '} {expected:30s} <- {desc[:60]}  (got {got})")
    print(f"Unseen merchant accuracy: {hits}/{len(UNSEEN_EXAMPLES)}")

    ml_model.train(save=True)
    print(f"Model saved to {ml_model.MODEL_FILE}")


if __name__ == "__main__":
    main()
