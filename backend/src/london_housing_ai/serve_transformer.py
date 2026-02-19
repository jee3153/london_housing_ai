import datetime
import json

import numpy as np
import pandas as pd


class ServingTransformer:
    """Transforms user input into model-ready features.

    Mirrors the training pipeline but uses precomputed lookup tables
    instead of computing trends from the full dataset
    """

    def __init__(self, lookup_path: str):
        with open(lookup_path) as f:
            tables = json.load(f)
        self._borough_price_trend = tables["borough_price_trend"]
        self._district_yearly_medians = tables["district_yearly_medians"]
        self._avg_price_last_half = tables["avg_price_last_half"]

    def transform(self, user_input: dict) -> pd.DataFrame:
        today = datetime.date.today()

        district = user_input["district"]
        property_type = user_input["property_type"]  # D/S/T/F
        is_new_build = user_input.get("is_new_build", "N")  # Y/N
        is_leasehold = user_input.get("is_leasehold", "N")  # Y/N
        sold_year = today.year
        sold_month = today.month

        # Trend lookups = use district median as fallback if district unseen
        global_price_median = np.median(list(self._borough_price_trend.values()))
        borough_price_trend = self._borough_price_trend.get(
            district, global_price_median
        )
        district_yearly_median = self._district_yearly_medians.get(
            f"{district}_{sold_year}",
            self._district_yearly_medians.get(
                f"{district}_{sold_year - 1}", global_price_median
            ),
        )
        avg_price_last_half = self._avg_price_last_half.get(
            district, global_price_median
        )

        # Interaction features - deterministic, same logic as training
        advanced_property_type = f"{is_new_build}_{property_type}"
        property_type_and_tenure = f"{is_leasehold}_{property_type}"
        property_type_and_district = f"{district}_{property_type}"

        row = {
            "property_type": property_type,
            "is_new_build": is_new_build,
            "is_leasehold": is_leasehold,
            "district": district,
            "sold_month": sold_month,
            "advanced_property_type": advanced_property_type,
            "property_type_and_tenure": property_type_and_tenure,
            "property_type_and_district": property_type_and_district,
            "date": float(datetime.date(sold_year, sold_month, 1).toordinal()),
            "sold_year": sold_year,
            "borough_price_trend": borough_price_trend,
            "district_yearly_medians": district_yearly_median,
            "avg_price_last_half": avg_price_last_half,
        }

        # Column order must match training exactly
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

        return pd.DataFrame([row])[required_cols]
