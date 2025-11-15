from typing import List
from pandas import DataFrame
import numpy as np
from sklearn.model_selection import train_test_split
from scipy.stats import ks_2samp
from london_housing_ai.utils.create_files import generate_artifact_from_payload


def generate_data_quality_report(df: DataFrame, filename: str):

    missing = df.isna().mean().sort_values(ascending=False).to_dict()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

    cat_cols = _categorical_columns(df)

    report = {
        "missing": {k: float(v) for k, v in missing.items()},
        "schema_summary": {k: str(v) for k, v in df.dtypes.to_dict().items()},
        "numeric_stats": df[numeric_cols].describe().astype(float).to_dict("records"),
        "outliers": {col: int(_count_outliers(df, col)) for col in numeric_cols},
        "train_val_drift": {
            col: float(ks_2samp(train_df[col].dropna(), val_df[col].dropna()).statistic)  # type: ignore
            for col in numeric_cols
        },
        "category_distribution": {
            col: {
                k: float(v)
                for k, v in df[col].value_counts(normalize=True).to_dict().items()
            }
            for col in cat_cols
        },
    }
    generate_artifact_from_payload(filename, report)


def _categorical_columns(df: DataFrame, max_unique: int = 50) -> List[str]:
    """Return categorical-like columns (object dtype and low cardinality)."""
    return [
        col
        for col in df.select_dtypes(include="object").columns
        if df[col].nunique() <= max_unique
    ]


def _count_outliers(df: DataFrame, column: str) -> int:
    Q1, Q3 = df[column].quantile([0.25, 0.75])
    IQR = Q3 - Q1
    lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
    return ((df[column] < lower) | (df[column] > upper)).sum()
