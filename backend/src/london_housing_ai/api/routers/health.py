from __future__ import annotations

from fastapi import APIRouter

from london_housing_ai.api.schemas import HealthResponse
from london_housing_ai.api.services import mlflow_service
from london_housing_ai.api.services.model_cache import get_or_load_model
from london_housing_ai.api.services.transformer_cache import get_or_load_transformer

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
        model_loaded = False
        transformer_loaded = False
        detail = None

        if latest_run_id:
            try:
                get_or_load_model(latest_run_id)
                model_loaded = True
            except Exception as e:
                detail = f"Model not loaded: {e}"
            try:
                get_or_load_transformer(latest_run_id)
                transformer_loaded = True
            except Exception as e:
                detail = f"Transformer not loaded: {e}"
        else:
            detail = "No finished runs found"

        status = (
            "ok" if (latest_run_id and model_loaded and transformer_loaded) else "degraded"
        )
        return HealthResponse(
            status=status,
            experiment_name=experiment_name,
            mlflow_tracking_uri=tracking_uri,
            latest_run_id=latest_run_id,
            model_loaded=model_loaded,
            transformer_loaded=transformer_loaded,
            detail=detail,
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            experiment_name=experiment_name,
            mlflow_tracking_uri=tracking_uri,
            latest_run_id=None,
            model_loaded=False,
            transformer_loaded=False,
            detail=str(e),
        )
