from typing import List
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
    extract_yearly_district_price_trend,
    extract_avg_price_last_6months,
    extract_interaction_features,
)
from src.config_schemas.CleaningConfig import CleaningConfig
from src.config_schemas.AugmentConfig import AugmentConfig
from src.config_schemas.FeatureConfig import FeatureConfig
from src.config_schemas.TrainConfig import TrainConfig
from ray_setup import configure_ray_for_repro
from ray.data import Dataset

configure_ray_for_repro()


def clean_dataset(ds: Dataset, cfg: CleaningConfig) -> Dataset:

    def _clean(pdf: DataFrame) -> DataFrame:
        pdf = numeric_cast(pdf, cfg.dtype_map)
        pdf = normalise_postcodes(pdf, raw_col=cfg.postcode_col)
        pdf = drop_na(pdf, subset=cfg.loading_cols)
        pdf = extract_sold_year(pdf, "date")
        pdf = extract_sold_month(pdf, "date")

        if cfg.clip_price:
            pdf["price"] = clip_upper_bound(pdf["price"], cfg.clip_quantile)
        for col_from, col_to in cfg.rename_cols.items():
            pdf = rename_column(pdf, col_from, col_to)
        return pdf

    return ds.map_batches(_clean, batch_format="pandas")


async def feature_engineer_dataset(
    ds: Dataset, fe_cfg: FeatureConfig, postcode_col: str
) -> Dataset:
    # level 1 extractions
    if fe_cfg.city_filter:
        filter_cfg = fe_cfg.city_filter
        ds = filter_by_keywords(ds, filter_cfg.filter_keywords, filter_cfg.city_col)
    if fe_cfg.use_district:
        ds = await get_district_from_postcode(ds, postcode_col, fe_cfg.district_col)

    # level 2 extractions
    ds = extract_borough_price_trend(
        ds=ds, extract_from=fe_cfg.timestamp_col, new_col="borough_price_trend"
    )
    ds = extract_yearly_district_price_trend(
        ds=ds,
        district_col="district",
        years_col="sold_year",
        new_col="district_yearly_medians",
    )
    ds = extract_avg_price_last_6months(
        ds=ds,
        new_col="avg_price_last_half",
        date_col=fe_cfg.timestamp_col,
        district_col=fe_cfg.district_col,
    )
    df = extract_interaction_features(
        ds=ds,
        combi_col_name="advanced_property_type",
        col1="is_new_build",
        col2="property_type",
    )
    df = extract_interaction_features(
        ds=ds,
        combi_col_name="property_type_and_tenure",
        col1="is_leasehold",
        col2="property_type",
    )
    df = extract_interaction_features(
        ds=ds,
        combi_col_name="property_type_and_district",
        col1="district",
        col2="property_type",
    )
    # add versioning here
    return ds


def build_aug_dataset(df: DataFrame, cfg: AugmentConfig) -> DataFrame:
    df = numeric_cast(df, cfg.dtype_map)
    df = normalise_postcodes(df, raw_col=cfg.postcode_col)
    df = drop_na(df, subset=cfg.required_cols)
    return df


def ds_with_required_cols(ds: Dataset, train_cfg: TrainConfig) -> Dataset:
    original_cols = ds.columns()
    if original_cols is None:
        original_cols = []
    original_cols_set = set(original_cols)
    required_cols_set = set(
        [
            *train_cfg.cat_features,
            *train_cfg.numeric_features,
            train_cfg.label,
        ]
    )

    intersection = original_cols_set.intersection(required_cols_set)

    if intersection != required_cols_set:
        raise KeyError(
            f"df column has missing columns: {required_cols_set.difference(intersection)}."
            + "If you changed logic on the same day, consider dropping table with today date and dataset_hashes table and rerun train."
        )
    return ds.select_columns(list(required_cols_set))
