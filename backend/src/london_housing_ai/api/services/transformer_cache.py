from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from london_housing_ai.api.services import mlflow_service
from london_housing_ai.serve_transformer import ServingTransformer

_lock = threading.Lock()
_cached_run_id: Optional[str] = None
_cached_transformer: Optional[ServingTransformer] = None


def _lookup_artifact_name() -> str:
    return os.getenv("LOOKUP_TABLE_ARTIFACT", "lookup_tables.json")


def _tracking_root_path() -> Optional[Path]:
    tracking_uri = mlflow_service.get_tracking_uri()
    if not tracking_uri:
        return None
    parsed = urlparse(tracking_uri)
    if parsed.scheme != "file":
        return None
    return Path(parsed.path)


def _local_lookup_path(run_id: str) -> Path:
    configured_file = os.getenv("LOOKUP_TABLE_FILE")
    if configured_file:
        return Path(configured_file)

    lookup_name = _lookup_artifact_name()
    tracking_root = _tracking_root_path()
    if tracking_root is not None:
        return tracking_root / run_id / "artifacts" / lookup_name
    return Path("/app") / run_id / "artifacts" / lookup_name


def _download_lookup_table(run_id: str) -> str:
    lookup_name = _lookup_artifact_name()
    try:
        return mlflow_service.download_artifact_for_run(
            run_id, lookup_name, tempfile.gettempdir()
        )
    except Exception as mlflow_error:
        local_path = _local_lookup_path(run_id)
        if local_path.exists():
            return str(local_path)
        raise RuntimeError(
            "Failed to load lookup table artifact "
            f"'{lookup_name}' for run '{run_id}': {mlflow_error}; "
            f"local fallback '{local_path}' not found"
        ) from mlflow_error


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
