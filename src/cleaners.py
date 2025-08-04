import pandas as pd
from pandas import DataFrame, Series
from typing import List, Dict

POSTCODE_CLEAN = "postcode_clean"


def canon_postcode(series: Series) -> Series:
    return (
        series.astype("string")  # guarantee string dtype
        .str.upper()  # SW1A 1AA → SW1A 1AA
        .str.replace(r"\s+", "", regex=True)  # kill *every* space → SW1A1AA
        .str.strip()  # trim lingering whitespace
    )


def numeric_cast(df: DataFrame, dtype_map: Dict[str, str]) -> DataFrame:
    for column, dtype in dtype_map.items():
        if dtype == "float":
            df[column] = pd.to_numeric(df[column], errors="coerce")
        elif dtype == "datetime":
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def normalise_postcodes(df: DataFrame, raw_col: str = "postal_code") -> DataFrame:
    out = df.copy()
    out[POSTCODE_CLEAN] = canon_postcode(out[raw_col])
    out["outcode"] = out[POSTCODE_CLEAN].str[:-3]
    out["incode"] = out[POSTCODE_CLEAN].str[-3:]

    return out


def clip_upper_bound(series: Series, quantile_percentage: float) -> Series:
    return series.clip(upper=series.quantile(quantile_percentage))


def drop_na(df: DataFrame, subset: List[str] | None = None) -> DataFrame:
    return df.dropna(subset=subset)


def rename_column(df: DataFrame, col_from: str, col_to: str) -> DataFrame:
    try:
        return df.rename(columns={col_from: col_to}, errors="raise").copy()
    except KeyError as e:
        print(f"Rename failed because {e}")
        return df
