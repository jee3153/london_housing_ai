import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

from london_housing_ai.config_schemas.TrainConfig import TrainConfig
from london_housing_ai.experiment_logger import ExperimentLogger
from london_housing_ai.models import PriceModel


def test_mlflow_logging_end_to_end(tmp_path):
    # Prepare a tiny dataset
    df = pd.DataFrame(
        {
            "bedrooms": [1, 2, 3, 2, 4, 3],
            "sqft": [350, 550, 700, 500, 900, 750],
            "price": [200000, 300000, 400000, 310000, 450000, 380000],
        }
    )

    # Minimal training config
    cfg = TrainConfig(
        n_iter=5,
        depth=3,
        lr=0.1,
        early_stop=2,
        random_state=42,
        label="price",
        cat_features=[],
        test_size=0.3,
        val_size=0.2,
        clip_target_q=0.99,
        log_target=False,
        numeric_features=["bedrooms", "sqft", "price"],
    )

    # Point MLflow to a temporary directory
    tracking_dir = tmp_path / "mlruns"
    mlflow.set_tracking_uri(f"file://{tracking_dir}")

    # Run training
    model = PriceModel(cfg)
    model.train_and_evaluate(df, checksum="dummy123")

    with mlflow.start_run(run_name="unit_test") as run:
        logger = ExperimentLogger(model, run)
        logger.log_all()

    # Verify logs exist
    client = MlflowClient(tracking_uri=f"file://{tracking_dir}")
    experiment = client.get_experiment_by_name("Default")
    if experiment is None:
        exp_id = client.create_experiment("Default")
    else:
        exp_id = experiment.experiment_id

    runs = client.search_runs(experiment_ids=[exp_id])
    assert runs, "No runs found in MLflow tracking directory."

    run_id = runs[0].info.run_id
    params = client.get_run(run_id).data.params
    metrics = client.get_run(run_id).data.metrics
    artifacts = client.list_artifacts(run_id)

    # Check that all categories were logged
    assert "learning_rate" in params
    assert "rmse" in metrics
    artifact_names = [a.path for a in artifacts]
    assert any("feature_importance" in n for n in artifact_names)
