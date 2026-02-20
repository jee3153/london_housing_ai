from __future__ import annotations

import datetime as dt
import os
from functools import lru_cache
from typing import List, Optional

import mlflow
import mlflow.catboost as mlflow_catboost
from mlflow.entities import Experiment, Run, RunStatus
from mlflow.tracking import MlflowClient

from london_housing_ai.api.schemas import ArtifactSummary, RunSummary


def get_tracking_uri() -> Optional[str]:
    return os.getenv("MLFLOW_TRACKING_URI")


def get_experiment_name() -> str:
    return os.getenv("MLFLOW_EXPERIMENT_NAME", "LondonHousingAI")


def get_artifact_path() -> str:
    return os.getenv("MLFLOW_ARTIFACT_PATH", "catboost_model")


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
    return mlflow_catboost.load_model(model_uri)


def download_artifact_for_run(
    run_id: str, artifact_path: str, dst_path: Optional[str] = None
) -> str:
    client = get_client()
    return client.download_artifacts(run_id, artifact_path, dst_path)


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
