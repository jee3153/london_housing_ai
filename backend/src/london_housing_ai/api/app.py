from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from london_housing_ai.api.routers.health import router as health_router
from london_housing_ai.api.routers.mlflow import router as mlflow_router
from london_housing_ai.api.routers.predict import router as predict_router
from london_housing_ai.api.services import mlflow_service
from london_housing_ai.api.services.model_cache import get_or_load_model
from london_housing_ai.api.services.transformer_cache import warmup_transformer
from london_housing_ai.utils.logger import get_logger

logger = get_logger()


def _parse_csv_env(name: str, default: List[str]) -> List[str]:
    raw = os.getenv(name)
    if raw is None:
        return default
    values = [part.strip() for part in raw.split(",")]
    return [value for value in values if value]


def _add_cors(app: FastAPI) -> None:
    allow_origins = _parse_csv_env("CORS_ALLOW_ORIGINS", ["http://localhost:5173"])
    allow_methods = _parse_csv_env("CORS_ALLOW_METHODS", ["*"])
    allow_headers = _parse_csv_env("CORS_ALLOW_HEADERS", ["*"])
    allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
    )


def create_app() -> FastAPI:
    title = os.getenv("API_TITLE", "London Housing Price Predictor")
    app = FastAPI(title=title)

    _add_cors(app)

    app.include_router(health_router)
    app.include_router(predict_router)
    app.include_router(mlflow_router)

    @app.on_event("startup")
    def _warmup_prediction_dependencies() -> None:
        try:
            run_id = mlflow_service.get_latest_finished_run_id()
            if run_id:
                get_or_load_model(run_id)
                warmup_transformer(run_id)
        except Exception:
            logger.exception("Failed to preload latest prediction dependencies")

    return app
