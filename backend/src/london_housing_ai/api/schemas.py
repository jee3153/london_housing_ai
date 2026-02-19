from __future__ import annotations

import datetime as dt
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class PredictResponse(BaseModel):
    predicted_price: float
    run_id: str


class ArtifactSummary(BaseModel):
    path: str
    is_dir: bool
    file_size: Optional[int] = None


class RunSummary(BaseModel):
    run_id: str
    status: str
    start_time: Optional[dt.datetime] = None
    end_time: Optional[dt.datetime] = None


class RunsResponse(BaseModel):
    experiment_name: str
    runs: List[RunSummary]


class ArtifactsResponse(BaseModel):
    run_id: str
    artifacts: List[ArtifactSummary]


class HealthResponse(BaseModel):
    status: str
    experiment_name: str
    mlflow_tracking_uri: Optional[str] = None
    latest_run_id: Optional[str] = None
    detail: Optional[str] = None


class PredictionRequest(BaseModel):
    postcode: str  # -> resolved to district via postcodes.io
    property_type: str  # D/S/T/F
    is_new_build: str = "N"  # Y/N
    is_leasehold: str = "N"  # Y/N (derived from duration field)

    @field_validator("property_type")
    @classmethod
    def validate_property_type(cls, v):
        allowed = {"D", "S", "T", "F"}
        if v.upper() not in allowed:
            raise ValueError(f"property_type must be one of {allowed}")
        return v.upper()

    @field_validator("is_new_build", "is_leasehold")
    @classmethod
    def validate_yn(cls, v):
        if v.upper() not in {"Y", "N"}:
            raise ValueError("Must be Y or N")
        return v.upper()
