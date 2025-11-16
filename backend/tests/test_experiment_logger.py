import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

from london_housing_ai.experiment_logger import ExperimentLogger
from london_housing_ai.models import PriceModel


class DummyModel(PriceModel):
    def __init__(self):
        self.log_data = {
            "params": {"learning_rate": "0.1"},
            "metrics": {"train_rmse": 0.5},
            "text": {"columns_used": ["sqft"]},
        }


def test_experiment_logger_uploads_artifacts(tmp_path):
    tracking_dir = tmp_path / "mlruns"
    mlflow.set_tracking_uri(f"file://{tracking_dir}")

    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "feature_importance.json").write_text("[]")
    (artifact_dir / "data_quality.json").write_text("{}")

    df = pd.DataFrame({"sqft": [400, 500], "price": [200000, 250000]})

    model = DummyModel()

    with mlflow.start_run(run_name="unit_test") as run:
        logger = ExperimentLogger(model, run, df, artifact_dir)
        logger.log_all()
        run_id = run.info.run_id

    client = MlflowClient(tracking_uri=f"file://{tracking_dir}")
    artifacts = client.list_artifacts(run_id)
    artifact_paths = sorted(a.path for a in artifacts)

    assert "feature_importance.json" in artifact_paths
    assert "data_quality.json" in artifact_paths
    assert "features.txt" in artifact_paths

    params = client.get_run(run_id).data.params
    metrics = client.get_run(run_id).data.metrics

    assert params["learning_rate"] == "0.1"
    assert metrics["train_rmse"] == 0.5
