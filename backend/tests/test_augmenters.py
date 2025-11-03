from pandas import DataFrame
from pandas.testing import assert_frame_equal

from london_housing_ai.augmenters import add_floor_area


def test_add_floor_area():
    price_col = {"price": [1, 2, 3]}
    postcode_col = {"postcode_clean": ["ABC", "DEF", "GHI"]}
    floor_area_col = {"floor_area": [4.4, 5.3, 6.1]}

    df = DataFrame({**price_col, **postcode_col})
    aug_df = DataFrame({**floor_area_col, **postcode_col})
    expected = DataFrame({**price_col, **postcode_col, **floor_area_col})

    assert_frame_equal(add_floor_area(df, aug_df, "floor_area"), expected)
