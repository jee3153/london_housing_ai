from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, Query

from london_housing_ai.api.schemas import ArtifactsResponse, MlflowRunRecord
from london_housing_ai.api.services import mlflow_service

router = APIRouter(prefix="/mlflow", tags=["mlflow"])


@router.get("/runs", response_model=List[MlflowRunRecord])
def runs(limit: int = Query(default=30, ge=1, le=200)) -> List[MlflowRunRecord]:
    return mlflow_service.list_runs_payload(limit=limit)


@router.get("/artifacts", response_model=ArtifactsResponse)
def artifacts(run_id: str | None = None) -> ArtifactsResponse:
    resolved_run_id = run_id or mlflow_service.get_latest_finished_run_id()
    if not resolved_run_id:
        raise HTTPException(status_code=503, detail="No trained runs available")
    return ArtifactsResponse(
        run_id=resolved_run_id, artifacts=mlflow_service.list_artifacts(resolved_run_id)
    )
