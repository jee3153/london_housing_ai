from pandas import DataFrame
from src.cleaners import (
    normalise_postcodes,
    numeric_cast,
    clip_upper_bound,
    drop_na,
    rename_column,
)
from src.feature_engineering import (
    get_district_from_postcode,
    filter_by_keywords,
    extract_sold_year,
    extract_sold_month,
    extract_borough_price_trend,
)
from src.config_schemas.CleaningConfig import CleaningConfig
from src.config_schemas.AugmentConfig import AugmentConfig
from src.config_schemas.FeatureConfig import FeatureConfig
from src.config_schemas.TrainConfig import TrainConfig


def clean_dataset(df: DataFrame, cfg: CleaningConfig) -> DataFrame:
    df = numeric_cast(df, cfg.dtype_map)
    df = normalise_postcodes(df, raw_col=cfg.postcode_col)
    df = drop_na(df, subset=cfg.loading_cols)
    df = extract_sold_year(df, "date")
    df = extract_sold_month(df, "date")

    if cfg.clip_price:
        df["price"] = clip_upper_bound(df["price"], cfg.clip_quantile)
    for col_from, col_to in cfg.rename_cols.items():
        df = rename_column(df, col_from, col_to)
    return df


async def feature_engineer_dataset(
    df: DataFrame, fe_cfg: FeatureConfig, postcode_col: str
) -> DataFrame:
    if fe_cfg.city_filter:
        filter_cfg = fe_cfg.city_filter
        df = filter_by_keywords(df, filter_cfg.filter_keywords, filter_cfg.city_col)
    if fe_cfg.use_district:
        df = await get_district_from_postcode(df, postcode_col, fe_cfg.district_col)
    df = extract_borough_price_trend(df, fe_cfg.timestamp_col)
    # add versioning here
    return df


def build_aug_dataset(df: DataFrame, cfg: AugmentConfig) -> DataFrame:
    df = numeric_cast(df, cfg.dtype_map)
    df = normalise_postcodes(df, raw_col=cfg.postcode_col)
    df = drop_na(df, subset=cfg.required_cols)
    return df


def df_with_required_cols(df: DataFrame, train_cfg: TrainConfig) -> DataFrame:
    copied_df = df.copy()
    required_cols = [
        *train_cfg.cat_features,
        *train_cfg.numeric_features,
        train_cfg.label,
    ]
    required_cols_set = set(required_cols)
    original_cols_set = set(copied_df.columns)
    intersection = original_cols_set.intersection(required_cols)

    if intersection != required_cols_set:
        raise KeyError(
            f"df column has missing columns: {required_cols_set.difference(intersection)}."
            + "If you changed logic on the same day, consider dropping table with today date and dataset_hashes table and rerun train."
        )
    return df[required_cols]
