from pathlib import Path
from london_housing_ai.utils.logger import get_logger
from london_housing_ai.models import PriceModel
import mlflow
from mlflow.tracking.fluent import ActiveRun

from typing import Optional, List

logger = get_logger()


class ExperimentLogger:
    def __init__(
        self, model: PriceModel, run: ActiveRun, output_dir: Optional[str] = None
    ):
        self.model = model
        self.run = run
        self.output_dir = Path(output_dir) if output_dir else None
        self.artifacts: List[Path] = model.log_data["artifacts"]

    def log_all(self) -> None:
        self.log_artifacts()
        self.log_params()
        self.log_metric()
        self.log_text()

    def log_artifacts(self) -> None:
        if not mlflow.active_run():
            mlflow.start_run(run_id=self.run.info.run_id)

        if self.artifacts:
            for artifact in self.artifacts:
                path = Path(artifact)
                if path.exists():
                    mlflow.log_artifact(str(path))
                    logger.info(f"Logged artifact: {path}")
                else:
                    logger.warning(f"ARtifact not found {path}")
        elif self.output_dir and self.output_dir.exists():
            mlflow.log_artifacts(str(self.output_dir))
            logger.info(f"Logged all artifacts from {self.output_dir}")
        else:
            logger.warning("No artifacts or output directory found to log.")

    def log_params(self) -> None:
        mlflow.log_params(self.model.log_data["params"])

    def log_metric(self) -> None:
        mlflow.log_metrics(self.model.log_data["metrics"])

    def log_text(self) -> None:
        mlflow.log_text(
            "\n".join(self.model.log_data["text"]["columns_used"]), "features.txt"
        )
