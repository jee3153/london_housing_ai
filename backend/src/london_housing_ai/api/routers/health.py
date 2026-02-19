from __future__ import annotations

from fastapi import APIRouter

from london_housing_ai.api.schemas import HealthResponse
from london_housing_ai.api.services import mlflow_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report API health for model-serving readiness.

    This endpoint marks status as:
    - ``ok`` when at least one FINISHED run exists in the configured MLflow experiment
    - ``degraded`` when no finished run is available or MLflow lookup fails

    Intention: surface whether the API can serve predictions from a trained model,
    not just whether the web process is alive.
    """
    experiment_name = mlflow_service.get_experiment_name()
    tracking_uri = mlflow_service.get_tracking_uri()

    try:
        latest_run_id = mlflow_service.get_latest_finished_run_id()
        status = "ok" if latest_run_id else "degraded"
        detail = None if latest_run_id else "No finished runs found"
        return HealthResponse(
            status=status,
            experiment_name=experiment_name,
            mlflow_tracking_uri=tracking_uri,
            latest_run_id=latest_run_id,
            detail=detail,
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            experiment_name=experiment_name,
            mlflow_tracking_uri=tracking_uri,
            latest_run_id=None,
            detail=str(e),
        )
