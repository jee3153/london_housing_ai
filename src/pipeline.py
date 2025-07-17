from typing import List
from pandas import DataFrame
from cleaners import normalise_postcodes, numeric_cast, clip_upper_bound, drop_na
from feature_engineering import get_district_from_postcode, filter_by_keywords
from config_schemas.CleaningConfig import CleaningConfig
from config_schemas.AugmentConfig import AugmentConfig
from config_schemas.FeatureConfig import FeatureConfig
from config_schemas.TrainConfig import TrainConfig


def clean_dataset(df: DataFrame, cfg: CleaningConfig) -> DataFrame:
    df = numeric_cast(df, cfg.dtype_map)
    df = normalise_postcodes(df, raw_col=cfg.postcode_col)
    df = drop_na(df, subset=cfg.required_cols)
    if cfg.clip_price:
        df["price"] = clip_upper_bound(df["price"], cfg.clip_quantile)
    return df


async def feature_engineer_dataset(
    df: DataFrame, fe_cfg: FeatureConfig, postcode_col: str
) -> DataFrame:
    if fe_cfg.city_filter:
        filter_cfg = fe_cfg.city_filter
        df = filter_by_keywords(df, filter_cfg.filter_keywords, filter_cfg.city_col)
    if fe_cfg.use_district:
        df = await get_district_from_postcode(df, postcode_col, fe_cfg.district_col)

    return df


def build_aug_dataset(df: DataFrame, cfg: AugmentConfig) -> DataFrame:
    df = numeric_cast(df, cfg.dtype_map)
    df = normalise_postcodes(df, raw_col=cfg.postcode_col)
    df = drop_na(df, subset=cfg.required_cols)
    return df


def df_with_required_cols(df: DataFrame, train_cfg: TrainConfig) -> DataFrame:
    return df[train_cfg.cat_features + train_cfg.numeric_features]


def add_sold_year_column(df: DataFrame, timestamp_col: str) -> DataFrame:
    df["sold_year"] = df[timestamp_col].dt.year.astype("Int64")
    return df
