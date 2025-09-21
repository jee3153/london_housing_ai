import pandas as pd
from typing import Literal
from pandas import DataFrame
import ray
from ray.data.aggregate import Quantile
from config_schemas.AugmentConfig import JoinType

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


def _merge_match_rate(ds: ray.data.Dataset, column_name: str) -> float:
    non_null_count = ds.filter(lambda row: row[column_name] is not None).count()
    total_count = ds.count()
    return non_null_count / total_count if total_count > 0 else float("nan")


def add_floor_area(
    main_ds: ray.data.Dataset,
    aug_ds: ray.data.Dataset,
    floor_col: str,
    merge_key: str = "postcode_clean",
    join_type: JoinType = JoinType.LEFT_OUTER,
    min_match_rate: float | None = None,
) -> ray.data.Dataset:
    main_cols = main_ds.columns()
    aug_cols = aug_ds.columns()
    if (
        main_cols is None
        or aug_cols is None
        or merge_key not in main_cols
        or merge_key not in aug_cols
    ):
        raise KeyError(f"'{merge_key}' must exist in both DataFrames.")

    if floor_col is None or floor_col not in aug_cols:
        raise KeyError(f"'{floor_col}' column missing from augmented DataFrame.")

    def _map_column(df, column_name: str):
        return df.assign(
            **{column_name: pd.to_numeric(df[column_name], errors="coerce")}
        )

    aug_ds = aug_ds.map_batches(
        lambda df: _map_column(df, floor_col), batch_format="pandas"
    )

    # Aggregate to median
    agg_ds = aug_ds.groupby(merge_key).aggregate(
        Quantile(on=floor_col, q=0.5, alias_name="median_floor")
    )

    # Merge main_ds(left) + agg_ds(right)
    merged_ds = main_ds.join(
        agg_ds, join_type=join_type.value, num_partitions=200, on=(merge_key,)
    )

    # Count duplicates in right dataset
    dup_check = agg_ds.groupby(merge_key).count().filter(lambda row: row["count"] > 1)

    if dup_check.count() > 0:
        raise ValueError("Right side has duplicate keys! violates: m:1 join")

    merge_rate = _merge_match_rate(merged_ds, floor_col)

    print(f"Matched floor-area for {merge_rate:.1%} of rows")

    if min_match_rate and merge_rate < min_match_rate:
        raise ValueError(
            f"Match-rate {merge_rate:.2%} below threshold ({min_match_rate:.2%})"
        )

    return merged_ds
