from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from london_housing_ai.api.schemas import ArtifactsResponse, RunsResponse
from london_housing_ai.api.services import mlflow_service

router = APIRouter(prefix="/mlflow", tags=["mlflow"])


@router.get("/runs", response_model=RunsResponse)
def runs(limit: int = Query(default=30, ge=1, le=200)) -> RunsResponse:
    return RunsResponse(
        experiment_name=mlflow_service.get_experiment_name(),
        runs=mlflow_service.list_run_summaries(limit=limit),
    )


@router.get("/artifacts", response_model=ArtifactsResponse)
def artifacts(run_id: str | None = None) -> ArtifactsResponse:
    resolved_run_id = run_id or mlflow_service.get_latest_finished_run_id()
    if not resolved_run_id:
        raise HTTPException(status_code=503, detail="No trained runs available")
    return ArtifactsResponse(
        run_id=resolved_run_id, artifacts=mlflow_service.list_artifacts(resolved_run_id)
    )

