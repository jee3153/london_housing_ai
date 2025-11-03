from math import floor

from pandas import DataFrame, Series
from pandas.testing import assert_frame_equal, assert_series_equal

from london_housing_ai.cleaners import (
    canon_postcode,
    clip_upper_bound,
    drop_na,
    normalise_postcodes,
    numeric_cast,
)


def test_canon():
    s = Series(["sw1a 1aa", " SW1A1AA "])
    assert canon_postcode(s).nunique() == 1


def test_numeric_cast():
    df = DataFrame({"col1": ["1", "2", "3.5"]})
    expected = DataFrame({"col1": [1.0, 2.0, 3.5]})
    assert_frame_equal(numeric_cast(df, {"col1": "float"}), expected)


def test_normalise_postcodes():
    df = DataFrame({"postal_code": ["SW1 3NS", "N1 2LY"]})
    expected = DataFrame(
        {
            "postal_code": ["SW1 3NS", "N1 2LY"],
            "postcode_clean": ["SW13NS", "N12LY"],
            "outcode": ["SW1", "N1"],
            "incode": ["3NS", "2LY"],
        }
    ).reset_index(drop=True)
    result = normalise_postcodes(df).reset_index(drop=True)

    for col in expected.columns:
        result[col] = result[col].astype("object")
        expected[col] = expected[col].astype("object")

    assert_frame_equal(result, expected, check_like=True)


def test_clip_upper_bound():
    s = Series([1, 2, 3, 1000])
    expected = Series([1.0, 2.0, 3.0, _get_quantile(s)])
    assert_series_equal(clip_upper_bound(s, 0.99), expected)


def _get_quantile(series, q=0.99) -> float:
    position = (len(series) - 1) * q
    index_start = floor(position)
    return series[index_start] + (series[index_start + 1] - series[index_start]) * (
        position - index_start
    )


def test_drop_na():
    inp = DataFrame({"a": [1, None], "b": [1, 2]})
    out = drop_na(inp, subset=["a"])
    assert len(out) == 1
