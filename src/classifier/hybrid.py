"""
The final classifier: combines three sources, in this order.

1. USER CORRECTIONS - if the user already told us the category of this exact
   kind of transaction, use it (confidence 100%).
2. RULES          - keyword rules (confidence 95%).
3. ML MODEL       - TF-IDF + Logistic Regression for everything else
                    (confidence = model probability).

Anything with low confidence is marked "needs_review" so the user can check it.
"""

import pandas as pd

from src.classifier import ml_model
from src.classifier.rules import classify_by_rules

RULE_CONFIDENCE = 0.95
REVIEW_BELOW = 0.60      # confidence under this -> ask the user to review
UNKNOWN_BELOW = 0.30     # confidence under this -> category "Others"


def _load_corrections():
    """Return {normalised description: category} from the corrections file."""
    if not ml_model.CORRECTIONS_FILE.exists():
        return {}
    data = pd.read_csv(ml_model.CORRECTIONS_FILE)
    return {
        ml_model.normalise(d, k): c
        for d, k, c in zip(data["description"], data["direction"], data["category"])
    }


def classify(transactions):
    """Add category, confidence, method and needs_review to every transaction."""
    corrections = _load_corrections()
    pending = []
    for txn in transactions:
        key = ml_model.normalise(txn["description"], txn.get("direction"))
        rule_category, keyword = classify_by_rules(txn["description"], txn.get("direction"))
        if key in corrections:
            category, confidence, method = corrections[key], 1.0, "learned from user"
        elif rule_category:
            category, confidence, method = rule_category, RULE_CONFIDENCE, f"rule ({keyword.strip()})"
        else:
            pending.append(txn)
            continue
        txn.update(category=category, confidence=round(confidence, 2), method=method,
                   needs_review=confidence < REVIEW_BELOW)

    # Only run the model on rows that neither corrections nor rules resolved.
    ml_results = ml_model.predict(
        [t["description"] for t in pending], [t.get("direction") for t in pending]
    ) if pending else []
    for txn, (ml_category, ml_confidence) in zip(pending, ml_results):
        if ml_confidence >= UNKNOWN_BELOW:
            category, confidence, method = ml_category, ml_confidence, "ml model"
        else:
            category, confidence, method = "Others", ml_confidence, "ml model (unsure)"

        txn["category"] = category
        txn["confidence"] = round(confidence, 2)
        txn["method"] = method
        txn["needs_review"] = confidence < REVIEW_BELOW
    return transactions


def save_corrections(rows):
    """
    Save user corrections and retrain the model so it learns from them.
    `rows` is a list of dicts with description, direction, category.
    """
    new = pd.DataFrame(rows, columns=["description", "direction", "category"])
    if ml_model.CORRECTIONS_FILE.exists():
        old = pd.read_csv(ml_model.CORRECTIONS_FILE)
        new = pd.concat([old, new], ignore_index=True)
    new = new.drop_duplicates(subset=["description", "direction"], keep="last")
    ml_model.CORRECTIONS_FILE.parent.mkdir(exist_ok=True)
    new.to_csv(ml_model.CORRECTIONS_FILE, index=False)
    ml_model.retrain()
    return len(new)
