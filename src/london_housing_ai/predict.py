import datetime

import numpy as np
import pandas as pd


def transform_to_training_features(user_input: dict) -> pd.DataFrame:
    raw = pd.DataFrame([user_input])

    # --- Derived mappings ---
    today = datetime.date.today()
    raw["sold_year"] = today.year
    raw["sold_month"] = today.month
    raw["is_new_build"] = "N"
    raw["is_leasehold"] = "N"
    raw["district"] = raw.get("location", "UNKNOWN")
    raw["property_type"] = raw.get("house_type", "UNKNOWN")

    # Required columns in the right order
    required_cols = [
        "property_type",
        "is_new_build",
        "is_leasehold",
        "district",
        "sold_month",
        "advanced_property_type",
        "property_type_and_tenure",
        "property_type_and_district",
        "date",
        "sold_year",
        "borough_price_trend",
        "district_yearly_medians",
        "avg_price_last_half",
    ]

    # Defaults
    categorical_defaults = {
        "property_type": "UNKNOWN",
        "is_new_build": "N",
        "is_leasehold": "N",
        "district": "UNKNOWN",
        "sold_month": str(today.month),
        "advanced_property_type": "UNKNOWN",
        "property_type_and_tenure": "UNKNOWN",
        "property_type_and_district": "UNKNOWN",
    }

    numeric_defaults = {
        "date": today.toordinal(),  # simple numeric fallback
        "sold_year": today.year,
        "borough_price_trend": np.nan,
        "district_yearly_medians": np.nan,
        "avg_price_last_half": np.nan,
    }

    # Apply defaults
    for col in required_cols:
        if col not in raw or pd.isna(raw[col]).any():
            if col in categorical_defaults:
                raw[col] = categorical_defaults[col]
            elif col in numeric_defaults:
                raw[col] = numeric_defaults[col]

    # Force types
    categorical_cols = list(categorical_defaults.keys())
    numeric_cols = list(numeric_defaults.keys())

    raw[categorical_cols] = raw[categorical_cols].astype(str).fillna("UNKNOWN")
    raw[numeric_cols] = raw[numeric_cols].astype(float)

    return raw[required_cols]
