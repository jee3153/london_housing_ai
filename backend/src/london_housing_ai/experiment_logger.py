from pathlib import Path
from typing import List, Optional

import mlflow
from mlflow.tracking.fluent import ActiveRun
from mlflow.data.pandas_dataset import from_pandas
from london_housing_ai.models import PriceModel
from london_housing_ai.utils.logger import get_logger
from pandas import DataFrame

logger = get_logger()


class ExperimentLogger:
    def __init__(
        self,
        model: PriceModel,
        run: ActiveRun,
        dataset: DataFrame,
        artifact_dir: Path,
    ):
        self.model = model
        self.run = run
        self.dataset = from_pandas(dataset)

        # add all generated artifacts under /artifacts directory
        if artifact_dir.exists():
            self.artifact_dir = artifact_dir
            self.artifacts: List[str] = [
                p.name for p in artifact_dir.iterdir() if p.is_file()
            ]

    def log_all(self) -> None:
        self._log_artifacts()
        self._log_params()
        self._log_metric()
        self._log_text()
        self._log_data()

    def _log_artifacts(self) -> None:
        if not mlflow.active_run():
            mlflow.start_run(run_id=self.run.info.run_id)
        if not self.artifact_dir:
            logger.warning("No artifacts or output directory found to log.")
        if self.artifact_dir and self.artifact_dir.exists():
            mlflow.log_artifacts(str(self.artifact_dir))
            logger.info(f"Logged all artifacts from {self.artifact_dir}")

    def _log_params(self) -> None:
        mlflow.log_params(self.model.log_data["params"])

    def _log_metric(self) -> None:
        mlflow.log_metrics(self.model.log_data["metrics"])

    def _log_text(self) -> None:
        mlflow.log_text(
            "\n".join(self.model.log_data["text"]["columns_used"]), "features.txt"
        )

    def _log_data(self) -> None:
        mlflow.log_input(self.dataset, context="training")
