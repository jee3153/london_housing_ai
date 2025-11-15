import json

import pandas as pd
import pytest

from london_housing_ai.data_quality_reporter import generate_data_quality_report
from london_housing_ai.utils import create_files


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            "price": [100_000, 150_000, 175_000, 125_000, 210_000],
            "sqft": [350, 450, 550, 500, 600],
            "bedrooms": [1, 2, 3, 2, 3],
            "property_type": ["flat", "flat", "house", "flat", "house"],
        }
    )


def test_generate_data_quality_report_creates_serializable_payload(
    tmp_path, monkeypatch, sample_dataframe
):
    monkeypatch.setattr(create_files, "ARTIFACT_DIR", tmp_path)

    filename = "data_quality.json"
    generate_data_quality_report(sample_dataframe, filename)

    report_path = tmp_path / filename
    assert report_path.exists()

    payload = json.loads(report_path.read_text())

    # basic keys exist
    assert set(payload) == {
        "missing",
        "schema_summary",
        "numeric_stats",
        "outliers",
        "train_val_drift",
        "category_distribution",
    }

    assert isinstance(payload["missing"]["price"], float)
    assert isinstance(payload["outliers"]["price"], int)
    assert isinstance(payload["train_val_drift"]["price"], float)
    assert isinstance(
        payload["category_distribution"]["property_type"]["flat"], float
    )

    # numeric stats should be list of json-serializable dicts
    assert isinstance(payload["numeric_stats"], list)
    assert payload["numeric_stats"]
    assert all(isinstance(v, float) for v in payload["numeric_stats"][0].values())
