import pandas as pd
import pytest
from pandas.testing import assert_series_equal, assert_frame_equal
from datetime import datetime, timezone
from src.pipeline import add_sold_year_column, df_with_required_cols
from src.config_schemas.TrainConfig import TrainConfig


def test_add_sold_year_column():

    original_df = pd.DataFrame(
        {
            "timestamp": [
                datetime(2023, 5, 1, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2025, 12, 30, 12, 40, 23, tzinfo=timezone.utc),
                datetime(2022, 9, 22, 3, 4, 1, tzinfo=timezone.utc),
            ]
        }
    )

    actual = add_sold_year_column(original_df, "timestamp")
    expected = pd.Series([2023, 2025, 2022], name="sold_year")

    assert_series_equal(actual["sold_year"], expected)


def test_df_with_required_cols():

    train_config = TrainConfig(
        cat_features=["district"],
        numeric_features=["distance_from_centre"],
        label="price",
    )

    original_df = pd.DataFrame(
        {
            "district": ["oxford circus", "liverpool street", "shoreditch"],
            "distance_from_centre": [1, 2, 3],
            "price": [200, 300, 400],
            "built_year": [2012, 2014, 2021],
        }
    )
    actual = df_with_required_cols(original_df, train_config)
    expected = original_df[["district", "distance_from_centre", "price"]].copy()

    assert_frame_equal(actual, expected)


def test_df_missing_label():
    train_config = TrainConfig(
        cat_features=["district"],
        numeric_features=["distance_from_centre"],
        label="price",
    )

    original_df = pd.DataFrame(
        {
            "district": ["oxford circus", "liverpool street", "shoreditch"],
            "distance_from_centre": [1, 2, 3],
            "built_year": [2012, 2014, 2021],
        }
    )

    with pytest.raises(KeyError, match=r"df column has missing columns:"):
        df_with_required_cols(original_df, train_config)
