from typing import List, Union, Dict

import numpy as np
from pandas import DataFrame, Index
from scipy.stats import ks_2samp
from sklearn.model_selection import train_test_split

from london_housing_ai.utils.create_files import generate_artifact_from_payload
from decimal import Decimal, ROUND_HALF_UP
from numpy import integer, floating


def generate_data_quality_report(df: DataFrame, filename: str):
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

    cat_cols = _categorical_columns(df)

    report = {
        "missing": _build_missing_data(df),
        "schema_summary": {
            "counts": {"columns": str(len(df.columns)), "rows": str(len(df.index))},
            "columns": {k: str(v) for k, v in df.dtypes.to_dict().items()},
        },
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


def _build_missing_data(df: DataFrame) -> List[Dict[str, str]]:
    missing_count = df.isna().sum().sort_values(ascending=False).to_dict()
    missing_percentage = df.isna().mean().sort_values(ascending=False).to_dict()
    missing_data = []

    for count_pair, percentage_pair in zip(
        missing_count.items(), missing_percentage.items()
    ):
        col_name, count = count_pair
        _, percentage = percentage_pair
        missing_data.append(
            {
                "column": str(col_name),
                "count": str(count),
                "percentage": _truncate_numeric(percentage * 100),
            }
        )

    return missing_data


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
    elif column == "duration" and category_name in duration_code.keys():
        return duration_code[category_name]
    elif column == "old/new" and category_name in is_new_build.keys():
        return is_new_build[category_name]
    else:
        return category_name


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
    below_lower = df[column] < lower
    above_upper = df[column] > upper
    mask = below_lower | above_upper
    return str(Decimal(int(mask.sum())).quantize(Decimal("1")))
