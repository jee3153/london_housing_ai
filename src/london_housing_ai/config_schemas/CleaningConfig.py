from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CleaningConfig:
    postcode_col: str
    loading_cols: List[str]
    required_cols: List[str]
    rename_cols: Dict[str, str]
    dtype_map: Dict[str, str]  # e.g. {column_name: dtype}
    col_headers: List[str]
    clip_price: bool = True
    clip_quantile: float = 0.99
