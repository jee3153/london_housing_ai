import pandas as pd
from pandas.testing import assert_series_equal
from datetime import datetime, timezone
from src.pipeline import add_sold_year_column


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
