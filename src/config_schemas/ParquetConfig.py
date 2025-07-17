from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ParquetConfig:
    sold_timestamp_col: str
    silver_partition_cols: List[str]
