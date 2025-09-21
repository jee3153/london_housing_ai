from typing import List, Dict, Literal
from dataclasses import dataclass
from enum import Enum


class JoinType(Enum):
    LEFT_OUTER = "left_outer"
    INNER = "inner"
    FULL_OUTER = "full_outer"
    RIGHT_OUTER = "right_outer"


@dataclass(frozen=True)
class AugmentConfig:
    postcode_col: str
    floor_col: str
    required_cols: List[str]
    dtype_map: Dict[str, str]
    col_headers: List[str]
    join_type: JoinType = JoinType.LEFT_OUTER
    min_match_rate: float | None = None
