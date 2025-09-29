import pandas as pd
from pandas.testing import assert_frame_equal
from london_housing_ai.feature_engineering import extract_interaction_features


def test_extract_interaction_features():
    df = pd.DataFrame(
        {
            "is_animal": ["rabbit", "tiger", "pig"],
            "is_plant": ["cactus", "tree", "rose"],
        }
    )
    expected = df.assign(combi=df["is_animal"] + "_" + df["is_plant"])
    actual = extract_interaction_features(df, "combi", "is_animal", "is_plant")

    assert_frame_equal(actual, expected)
