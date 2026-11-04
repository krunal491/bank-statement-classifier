"""
Classifier part 2: a traditional MACHINE LEARNING model (no LLM).

How it works:
1. Clean the description: "UPI/DR/4123.../SWIGGY/YESB/swiggy@ybl" -> "UPI DR SWIGGY YESB SWIGGY YBL"
2. TF-IDF turns text into numbers. It looks at whole words AND at small
   pieces of words (character n-grams), so it still works when OCR makes a
   typo ("SWIGY") or for a merchant name it has never seen ("CAFE MOCHA").
3. Logistic Regression learns which words point to which category and gives
   a probability for every category. The highest probability is our
   "confidence".

Training data: data/training_data.csv (synthetic, see scripts/generate_training_data.py)
plus the corrections users make in the app (data/user_corrections.csv).
"""

import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[2]
TRAINING_FILE = ROOT / "data" / "training_data.csv"
CORRECTIONS_FILE = ROOT / "data" / "user_corrections.csv"
MODEL_FILE = ROOT / "models" / "classifier.joblib"


def normalise(description, direction=None):
    """Make the text easier for the model: uppercase, no digits, no symbols."""
    text = (description or "").upper()
    text = re.sub(r"\d+", " ", text)           # numbers carry no category meaning
    text = re.sub(r"[^A-Z ]+", " ", text)      # / - * @ . become spaces
    text = re.sub(r"\s+", " ", text).strip()
    if direction:
        text += f" __{direction.upper()}__"   # money in vs out is a useful hint
    return text


def build_model():
    features = FeatureUnion([
        ("words", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)),
    ])
    return Pipeline([
        ("features", features),
        ("classifier", LogisticRegression(max_iter=2000, C=8, class_weight="balanced")),
    ])


def load_training_data():
    """Synthetic training data + user corrections (corrections count 5x)."""
    data = pd.read_csv(TRAINING_FILE)
    if CORRECTIONS_FILE.exists():
        corrections = pd.read_csv(CORRECTIONS_FILE)
        if not corrections.empty:
            data = pd.concat([data] + [corrections[data.columns]] * 5, ignore_index=True)
    return data


def train(save=True):
    """Train the model and (optionally) save it to models/classifier.joblib."""
    data = load_training_data()
    texts = [normalise(d, k) for d, k in zip(data["description"], data["direction"])]
    model = build_model()
    model.fit(texts, data["category"])
    if save:
        MODEL_FILE.parent.mkdir(exist_ok=True)
        joblib.dump(model, MODEL_FILE)
    return model


_model = None


def get_model():
    """Load the saved model, or train a new one if it's missing/incompatible."""
    global _model
    if _model is None:
        try:
            _model = joblib.load(MODEL_FILE)
        except Exception:
            _model = train()
    return _model


def retrain():
    """Retrain after the user corrected some categories."""
    global _model
    _model = train()
    return _model


def predict(descriptions, directions):
    """Return a list of (category, confidence) for each description."""
    model = get_model()
    texts = [normalise(d, k) for d, k in zip(descriptions, directions)]
    if not texts:
        return []
    probabilities = model.predict_proba(texts)
    classes = model.classes_
    results = []
    for row in probabilities:
        best = row.argmax()
        results.append((classes[best], float(row[best])))
    return results
