from typing import List, Dict, Literal
from dataclasses import dataclass

@dataclass(frozen=True)
class AugmentConfig:
    postcode_col: str
    floor_col: str 
    required_cols: List[str] 
    dtype_map: Dict[str, str]
    col_headers: List[str]
    join_method: Literal['left', 'inner'] = 'left'
    min_match_rate: float | None = None
        

