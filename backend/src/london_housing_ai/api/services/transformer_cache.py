from __future__ import annotations

import os
import tempfile
import threading
from typing import Optional

from london_housing_ai.api.services import mlflow_service
from london_housing_ai.serve_transformer import ServingTransformer

_lock = threading.Lock()
_cached_run_id: Optional[str] = None
_cached_transformer: Optional[ServingTransformer] = None


def _artifact_candidates() -> list[str]:
    configured = os.getenv("LOOKUP_TABLE_ARTIFACT", "lookup_tables.json")
    if configured == "lookup_table.json":
        return [configured, "lookup_tables.json"]
    if configured == "lookup_tables.json":
        return [configured, "lookup_table.json"]
    return [configured]


def _download_lookup_table(run_id: str) -> str:
    errors: list[str] = []
    for artifact_path in _artifact_candidates():
        try:
            return mlflow_service.download_artifact_for_run(
                run_id, artifact_path, tempfile.gettempdir()
            )
        except Exception as e:
            errors.append(f"{artifact_path}: {e}")
    raise RuntimeError(
        "Failed to download lookup table artifact. " + " | ".join(errors)
    )


def get_or_load_transformer(run_id: str) -> ServingTransformer:
    global _cached_run_id, _cached_transformer
    with _lock:
        if _cached_transformer is not None and _cached_run_id == run_id:
            return _cached_transformer
        lookup_path = _download_lookup_table(run_id)
        transformer = ServingTransformer(lookup_path)
        _cached_run_id = run_id
        _cached_transformer = transformer
        return transformer


def warmup_transformer(run_id: str) -> None:
    get_or_load_transformer(run_id)
