from typing import Literal

import pandas as pd
from pandas import DataFrame

from london_housing_ai.utils.logger import get_logger

logger = get_logger()
"""
    Add median floor-area (ft²) from EPC data to the main PPD DataFrame.

    Parameters
    ----------
    main_df     : price-paid DataFrame that already has `merge_key`
    aug_df      : EPC DataFrame with the same `merge_key` and `floor_col`
    floor_col   : column in `aug_df` holding numeric floor-area
    merge_key   : cleaned postcode string used for join
    how         : 'left' keeps all main rows; 'inner' drops non-matches
    min_match_rate : if set, raise ValueError if match rate falls below threshold

    Returns
    -------
    merged_df   : main_df + one new column  (name = `floor_col`)
    """


def add_floor_area(
    main_df: DataFrame,
    aug_df: DataFrame,
    floor_col: str,
    merge_key: str = "postcode_clean",
    how: Literal["left", "inner"] = "left",
    min_match_rate: float | None = None,
) -> DataFrame:
    if merge_key not in main_df or merge_key not in aug_df:
        raise KeyError(f"'{merge_key}' must exist in both DataFrames.")

    if floor_col not in aug_df:
        raise KeyError(f"'{floor_col}' column missing from augmented DataFrame.")

    aug_df = aug_df.copy()
    aug_df[floor_col] = pd.to_numeric(aug_df[floor_col], errors="coerce")

    agg_df = aug_df.groupby(merge_key, as_index=False).agg(
        {floor_col: "median"}
    )  # aggregate to collapse duplicates on merge_key

    merged_df = main_df.merge(agg_df, on=merge_key, how=how, validate="m:1")

    match_rate = merged_df[floor_col].notna().mean()
    logger.info(f"Matched floor-area for {match_rate:.1%} of rows")

    if min_match_rate and match_rate < min_match_rate:
        raise ValueError(
            f"Match-rate {match_rate:.2%} below threshold ({min_match_rate:.2%})"
        )

    return merged_df
