from dataclasses import dataclass
from typing import Dict, List, Literal


@dataclass(frozen=True)
class AugmentConfig:
    postcode_col: str
    floor_col: str
    required_cols: List[str]
    dtype_map: Dict[str, str]
    col_headers: List[str]
    join_method: Literal["left", "inner"] = "left"
    min_match_rate: float | None = None
