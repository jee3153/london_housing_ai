from london_housing_ai.api import main_api
import pytest
import os

# @pytest.fixture(scope="module", autouse=True)
# def train_model(tmp_path_factory)
#     tracking_dir = tmp_path_factory.mktemp("mlruns")
#     artifacts_dir = tmp_path_factory.mktemp("mlartifacts")
#     os.environ["MLFLOW_TRACKING_URI"] = f"file://{tracking_dir}"
#     os.environ["MLFLOW_ARTIFACT_URI"] = f"file://{artifacts_dir}"


def test_data_quality_artifacts(request: pytest.FixtureRequest):
    main_api.get_data_quality_artifacts()
