"""JSON-safety helpers: pandas/numpy values don't serialize to JSON as-is (NaN, NaT,
numpy scalars, date objects all need converting)."""

import datetime
import math

import numpy as np
import pandas as pd


def clean(value):
    if value is None:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime.date, datetime.datetime)):
        try:
            if pd.isna(value):
                return None
        except TypeError:
            pass
        return value.isoformat()
    return value


def dict_clean(d):
    return {k: (v if isinstance(v, list) else clean(v)) for k, v in d.items()}


def df_records(df: pd.DataFrame):
    """DataFrame -> list of JSON-safe dicts, each with a stable `id` (its row position)."""
    if df is None or df.empty:
        return []
    safe = df.reset_index(drop=True)
    records = []
    for i, row in safe.iterrows():
        rec = {col: clean(row[col]) for col in safe.columns}
        rec["id"] = int(i)
        records.append(rec)
    return records
