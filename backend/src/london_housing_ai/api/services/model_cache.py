from __future__ import annotations

import threading
from typing import Any, Optional, Tuple

from london_housing_ai.api.services.mlflow_service import load_model_for_run

_lock = threading.Lock()
_cached_run_id: Optional[str] = None
_cached_model: Any = None


def get_or_load_model(run_id: str):
    global _cached_run_id, _cached_model
    with _lock:
        if _cached_model is not None and _cached_run_id == run_id:
            return _cached_model
        model = load_model_for_run(run_id)
        _cached_run_id = run_id
        _cached_model = model
        return model

