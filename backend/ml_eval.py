"""Baseline metrics from a separate 80/20 synthetic-data evaluation.

Generate with `python -m backend.ml_eval` during the image build. Requests read
only the packaged result; they never train a model or score production data.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from src.classifier import ml_model

METRICS_FILE = Path(__file__).with_name("model_metrics.json")


def _score(model, test_df):
    texts = [ml_model.normalise(d, k) for d, k in zip(test_df.description, test_df.direction)]
    predicted = model.predict(texts)
    report = classification_report(test_df.category, predicted, output_dict=True, zero_division=0)
    accuracy = report.pop("accuracy")
    report.pop("macro avg", None)
    report.pop("weighted avg", None)
    per_category = {
        category: {
            "precision": round(metrics["precision"], 3),
            "recall": round(metrics["recall"], 3),
            "f1": round(metrics["f1-score"], 3),
            "support": int(metrics["support"]),
        }
        for category, metrics in report.items()
    }
    return {"accuracy": round(accuracy, 4), "test_rows": len(test_df), "per_category": per_category}


def compute_baseline():
    """Build-time evaluation, independent of saved user corrections."""
    data = pd.read_csv(ml_model.TRAINING_FILE)
    train_df, test_df = train_test_split(data, test_size=0.2, random_state=0, stratify=data["category"])
    model = ml_model.build_model()
    texts = [ml_model.normalise(d, k) for d, k in zip(train_df.description, train_df.direction)]
    model.fit(texts, train_df.category)
    return _score(model, test_df)


def baseline_eval():
    """Read packaged metrics without doing expensive work on an API request."""
    artifact = json.loads(METRICS_FILE.read_text())
    if artifact["dataset_sha256"] != hashlib.sha256(ml_model.TRAINING_FILE.read_bytes()).hexdigest():
        raise ValueError("Evaluation artifact does not match training data")
    return artifact["baseline"]


if __name__ == "__main__":
    artifact = {
        "dataset_sha256": hashlib.sha256(ml_model.TRAINING_FILE.read_bytes()).hexdigest(),
        "baseline": compute_baseline(),
    }
    METRICS_FILE.write_text(json.dumps(artifact, indent=2) + "\n")
