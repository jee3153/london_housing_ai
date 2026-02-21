from __future__ import annotations

import datetime as dt
import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import mlflow.catboost as mlflow_catboost
from mlflow.entities import Experiment, Run, RunStatus
from mlflow.tracking import MlflowClient

from london_housing_ai.api.schemas import ArtifactSummary, RunSummary


def _normalize_tracking_uri(uri: Optional[str]) -> Optional[str]:
    if not uri:
        return uri
    value = uri.strip()
    if value.startswith("file://") and not value.startswith("file:///"):
        parsed = urlparse(value)
        if parsed.netloc:
            return f"file:///{parsed.netloc}{parsed.path}"
    return value


def get_tracking_uri() -> Optional[str]:
    return _normalize_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))


def _tracking_local_path() -> Optional[Path]:
    tracking_uri = get_tracking_uri()
    if not tracking_uri:
        return None
    parsed = urlparse(tracking_uri)
    if parsed.scheme != "file":
        return None
    return Path(parsed.path)


def _run_artifact_path(run_id: str, artifact_path: str) -> Optional[Path]:
    root = _tracking_local_path()
    if root is None:
        return None
    return root / run_id / "artifacts" / artifact_path


def _model_artifacts_dir_for_run(run_id: str) -> Optional[Path]:
    root = _tracking_local_path()
    if root is None:
        return None
    models_dir = root / "models"
    if not models_dir.exists():
        return None

    for model_dir in models_dir.iterdir():
        if not model_dir.is_dir():
            continue
        artifacts_dir = model_dir / "artifacts"
        mlmodel_path = artifacts_dir / "MLmodel"
        if not mlmodel_path.exists():
            continue
        try:
            content = mlmodel_path.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in content.splitlines():
            if line.startswith("run_id:") and line.split(":", 1)[1].strip() == run_id:
                return artifacts_dir
    return None


def get_experiment_name() -> str:
    return os.getenv("MLFLOW_EXPERIMENT_NAME", "LondonHousingAI")


def get_artifact_path() -> str:
    return os.getenv("MLFLOW_ARTIFACT_PATH", "catboost_model")


def get_model_dir() -> Optional[str]:
    return os.getenv("MLFLOW_MODEL_DIR")


@lru_cache(maxsize=1)
def get_client() -> MlflowClient:
    tracking_uri = get_tracking_uri()
    if tracking_uri:
        return MlflowClient(tracking_uri=tracking_uri)
    return MlflowClient()


def _to_dt_utc(ms: Optional[int]) -> Optional[dt.datetime]:
    if ms is None:
        return None
    return dt.datetime.fromtimestamp(ms / 1000.0, tz=dt.timezone.utc)


def get_experiment(client: MlflowClient, name: str) -> Optional[Experiment]:
    try:
        return client.get_experiment_by_name(name)
    except Exception:
        return None


def list_recent_finished_runs(
    client: MlflowClient, experiment_id: str, limit: int = 30
) -> List[Run]:
    """Return up to ``limit`` FINISHED runs for one experiment.

    In MLflow, one experiment contains many runs. ``experiment_id`` identifies
    that single experiment, and ``search_runs`` expects a list of experiment IDs,
    so we pass ``[experiment_id]``.
    """
    finished_status = RunStatus.to_string(RunStatus.FINISHED)
    return client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=f"attributes.status = '{finished_status}'",
        order_by=["start_time DESC"],
        max_results=limit,
    )


def get_latest_finished_run_id() -> Optional[str]:
    # Allow hardcoding for Railway deployment where no MLflow server exists
    hardcoded = os.getenv("MLFLOW_RUN_ID")
    if hardcoded:
        return hardcoded

    client = get_client()
    experiment = get_experiment(client, get_experiment_name())
    if experiment is None:
        return None
    runs = list_recent_finished_runs(client, experiment.experiment_id, limit=1)
    if not runs:
        return None
    return runs[0].info.run_id


def list_run_summaries(limit: int = 30) -> List[RunSummary]:
    client = get_client()
    experiment = get_experiment(client, get_experiment_name())
    if experiment is None:
        return []
    runs = list_recent_finished_runs(client, experiment.experiment_id, limit=limit)
    return [
        RunSummary(
            run_id=run.info.run_id,
            status=run.info.status,
            start_time=_to_dt_utc(run.info.start_time),
            end_time=_to_dt_utc(run.info.end_time),
        )
        for run in runs
    ]


def list_artifacts(run_id: str) -> List[ArtifactSummary]:
    client = get_client()
    infos = client.list_artifacts(run_id)
    return [
        ArtifactSummary(path=info.path, is_dir=info.is_dir, file_size=info.file_size)
        for info in infos
    ]


def list_artifacts_payload(run_id: str):
    return [artifact.model_dump() for artifact in list_artifacts(run_id)]


def list_runs_payload(limit: int = 30):
    client = get_client()
    experiment = get_experiment(client, get_experiment_name())
    if experiment is None:
        return []
    runs = list_recent_finished_runs(client, experiment.experiment_id, limit=limit)

    payload = []
    for run in runs:
        info = run.info
        data = run.data
        payload.append(
            {
                "data": {
                    "metrics": dict(data.metrics or {}),
                    "params": dict(data.params or {}),
                    "tags": dict(data.tags or {}),
                },
                "info": {
                    "artifact_uri": getattr(info, "artifact_uri", None),
                    "end_time": info.end_time,
                    "experiment_id": info.experiment_id,
                    "lifecycle_stage": getattr(info, "lifecycle_stage", None),
                    "run_id": info.run_id,
                    "run_uuid": getattr(info, "run_uuid", info.run_id),
                    "start_time": info.start_time,
                    "status": info.status,
                    "user_id": getattr(info, "user_id", None),
                },
            }
        )
    return payload


def load_model_for_run(run_id: str):
    artifact_path = get_artifact_path()
    model_uri = f"runs:/{run_id}/{artifact_path}"
    try:
        return mlflow_catboost.load_model(model_uri)
    except Exception:
        configured_model_dir = get_model_dir()
        if configured_model_dir and Path(configured_model_dir).exists():
            return mlflow_catboost.load_model(configured_model_dir)
        model_for_run_dir = _model_artifacts_dir_for_run(run_id)
        if model_for_run_dir and model_for_run_dir.exists():
            return mlflow_catboost.load_model(str(model_for_run_dir))
        direct_model_dir = _run_artifact_path(run_id, artifact_path)
        if direct_model_dir and direct_model_dir.exists():
            return mlflow_catboost.load_model(str(direct_model_dir))
        raise


def download_artifact_for_run(
    run_id: str, artifact_path: str, dst_path: Optional[str] = None
) -> str:
    try:
        client = get_client()
        return client.download_artifacts(run_id, artifact_path, dst_path)
    except Exception:
        direct_artifact = _run_artifact_path(run_id, artifact_path)
        if not direct_artifact or not direct_artifact.exists():
            raise
        return str(direct_artifact)


def run_uses_log_target(run_id: str, default: bool = True) -> bool:
    """Read log_target from run params; fallback to default for older runs."""
    try:
        run = get_client().get_run(run_id)
        raw = (run.data.params or {}).get("log_target")
        if raw is None:
            return default
        return str(raw).strip().lower() in {"1", "true", "yes", "y"}
    except Exception:
        return default
