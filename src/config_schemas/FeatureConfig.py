from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CityFilter:
    city_col: str
    filter_keywords: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class FeatureConfig:
    use_district: bool = False
    district_col: str = "district"
    drop_niche_threshold: int = 10
    city_filter: CityFilter | None = None
