from __future__ import annotations

import os
import threading
from typing import Optional

from london_housing_ai.serve_transformer import ServingTransformer

_lock = threading.Lock()
_cached_lookup_path: Optional[str] = None
_cached_transformer: Optional[ServingTransformer] = None


def get_lookup_path() -> str:
    return os.getenv("LOOKUP_TABLE_PATH", "artifacts/lookup_tables.json")


def get_or_load_transformer() -> ServingTransformer:
    global _cached_lookup_path, _cached_transformer
    lookup_path = get_lookup_path()
    with _lock:
        if _cached_transformer is not None and _cached_lookup_path == lookup_path:
            return _cached_transformer
        transformer = ServingTransformer(lookup_path)
        _cached_lookup_path = lookup_path
        _cached_transformer = transformer
        return transformer


def warmup_transformer() -> None:
    get_or_load_transformer()
