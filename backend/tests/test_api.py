import datetime as dt

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from london_housing_ai.api.app import create_app
from london_housing_ai.api.schemas import ArtifactSummary
from london_housing_ai.api.services import mlflow_service


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://example.com")
    app = create_app()
    return TestClient(app)


def test_cors_allows_configured_origin(client: TestClient) -> None:
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in (200, 204)
    assert resp.headers.get("access-control-allow-origin") == "http://example.com"


def test_health_degraded_when_no_runs(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    import london_housing_ai.api.routers.health as health_router

    monkeypatch.setattr(
        mlflow_service, "get_experiment_name", lambda: "LondonHousingAI"
    )
    monkeypatch.setattr(
        mlflow_service, "get_tracking_uri", lambda: "http://mlflow:5000"
    )
    monkeypatch.setattr(mlflow_service, "get_latest_finished_run_id", lambda: None)
    monkeypatch.setattr(health_router, "get_or_load_transformer", lambda: object())

    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "degraded"
    assert payload["latest_run_id"] is None
    assert payload["model_loaded"] is False
    assert payload["transformer_loaded"] is False


def test_health_ok_when_latest_run_exists(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    import london_housing_ai.api.routers.health as health_router

    monkeypatch.setattr(
        mlflow_service, "get_experiment_name", lambda: "LondonHousingAI"
    )
    monkeypatch.setattr(
        mlflow_service, "get_tracking_uri", lambda: "http://mlflow:5000"
    )
    monkeypatch.setattr(mlflow_service, "get_latest_finished_run_id", lambda: "run123")
    monkeypatch.setattr(
        health_router, "get_or_load_transformer", lambda run_id: object()
    )
    monkeypatch.setattr(health_router, "get_or_load_model", lambda run_id: object())

    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["latest_run_id"] == "run123"
    assert payload["model_loaded"] is True
    assert payload["transformer_loaded"] is True


def test_predict_success(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    import london_housing_ai.api.routers.predict as predict_router

    class DummyModel:
        def predict(self, features):
            return np.array([np.log1p(1000.0)])

    class DummyTransformer:
        def transform(self, user_input):
            return pd.DataFrame([user_input])

    async def fake_resolve_district(postcode: str):
        return "Camden"

    monkeypatch.setattr(mlflow_service, "get_latest_finished_run_id", lambda: "run123")
    monkeypatch.setattr(
        mlflow_service, "run_uses_log_target", lambda run_id, default=True: True
    )
    monkeypatch.setattr(
        predict_router, "get_or_load_model", lambda run_id: DummyModel()
    )
    monkeypatch.setattr(
        predict_router, "get_or_load_transformer", lambda run_id: DummyTransformer()
    )
    monkeypatch.setattr(predict_router, "resolve_district", fake_resolve_district)

    resp = client.post(
        "/predict",
        json={
            "postcode": "EC1A1BB",
            "property_type": "F",
            "is_new_build": "N",
            "is_leasehold": "N",
        },
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["run_id"] == "run123"
    assert payload["predicted_price"] == 1000.0
    assert payload["confidence_interval"] == [900.0, 1100.0]
    assert payload["model_version"].endswith(":run123")
    assert "user_provided" in payload["features_used"]
    assert "enriched" in payload["features_used"]
    assert "defaulted" in payload["features_used"]


def test_mlflow_runs_endpoint(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    runs = [
        {
            "data": {
                "metrics": {"validation_rmse": 123.45},
                "params": {"model_class": "CatBoostRegressor"},
                "tags": {"mlflow.runName": "run-1"},
            },
            "info": {
                "artifact_uri": "mlflow-artifacts:/0/run1/artifacts",
                "end_time": 1735689900000,
                "experiment_id": "0",
                "lifecycle_stage": "active",
                "run_id": "run1",
                "run_uuid": "run1",
                "start_time": 1735689600000,
                "status": "FINISHED",
                "user_id": "tester",
            },
        }
    ]
    monkeypatch.setattr(
        mlflow_service, "list_runs_payload", lambda limit=30: runs[:limit]
    )

    resp = client.get("/mlflow/runs?limit=1")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload[0]["info"]["run_id"] == "run1"
    assert payload[0]["data"]["params"]["model_class"] == "CatBoostRegressor"


def test_mlflow_artifacts_endpoint(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    artifacts = [ArtifactSummary(path="catboost_model", is_dir=True, file_size=None)]
    monkeypatch.setattr(mlflow_service, "get_latest_finished_run_id", lambda: "run123")
    monkeypatch.setattr(mlflow_service, "list_artifacts", lambda run_id: artifacts)

    resp = client.get("/mlflow/artifacts")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["run_id"] == "run123"
    assert payload["artifacts"][0]["path"] == "catboost_model"
