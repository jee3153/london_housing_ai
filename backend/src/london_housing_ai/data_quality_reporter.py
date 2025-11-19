from typing import List, Union

import numpy as np
from pandas import DataFrame, Index
from scipy.stats import ks_2samp
from sklearn.model_selection import train_test_split

from london_housing_ai.utils.create_files import generate_artifact_from_payload
from decimal import Decimal, ROUND_HALF_UP
from numpy import integer, floating


def generate_data_quality_report(df: DataFrame, filename: str):

    missing = df.isna().mean().sort_values(ascending=False).to_dict()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

    cat_cols = _categorical_columns(df)

    report = {
        "missing": {k: _truncate_numeric(v) for k, v in missing.items()},
        "schema_summary": {k: str(v) for k, v in df.dtypes.to_dict().items()},
        "numeric_stats": _build_numeric_stats(df, numeric_cols),
        "outliers": {col: _count_outliers(df, col) for col in numeric_cols},
        "train_val_drift": {
            col: _truncate_numeric(ks_2samp(train_df[col].dropna(), val_df[col].dropna()).statistic)  # type: ignore
            for col in numeric_cols
        },
        "category_distribution": {
            col: {
                _convert_to_readable_cat(k, col): _truncate_numeric(v)
                for k, v in df[col].value_counts(normalize=True).to_dict().items()
            }
            for col in cat_cols
        },
    }

    generate_artifact_from_payload(filename, report)


def _convert_to_readable_cat(category_name: str, column: str) -> str:
    property_type_code = {
        "D": "Detached",
        "S": "Semi-detached",
        "T": "Terraced",
        "F": "Flats / maisonette",
        "O": "Other",
    }
    duration_code = {"F": "Freehold", "L": "Leasehold"}
    is_new_build = {"N": "Historic property", "Y": "New build"}
    if column == "property_type" and category_name in property_type_code.keys():
        return property_type_code[category_name]
    if column == "duration" and category_name in duration_code.keys():
        return duration_code[category_name]
    if column == "old/new" and category_name in is_new_build.keys():
        return is_new_build[category_name]
    raise NameError(f"Following category name: {category_name} doesn't exist.")


def _truncate_numeric(value: Union[int, float, integer, floating]) -> str:
    return str(Decimal(str(value)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))


def _build_numeric_stats(df: DataFrame, numeric_cols: Index):
    stats = []
    for col in numeric_cols:
        stat = {
            "column": col,
        }
        series = df[col].describe()
        for index, value in zip(series.index, series.values):
            stat[index] = _truncate_numeric(value)
        stats.append(stat)
    return stats


def _categorical_columns(df: DataFrame, max_unique: int = 50) -> List[str]:
    """Return categorical-like columns (object dtype and low cardinality)."""
    return [
        col
        for col in df.select_dtypes(include="object").columns
        if df[col].nunique() <= max_unique
    ]


def _count_outliers(df: DataFrame, column: str) -> str:
    Q1, Q3 = df[column].quantile([0.25, 0.75])
    IQR = Q3 - Q1
    lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
    return _truncate_numeric(((df[column] < lower) | (df[column] > upper)).sum())
