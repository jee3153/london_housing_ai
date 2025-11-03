from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TrainConfig:
    cat_features: List[str]
    numeric_features: List[str]
    label: str
    log_target: bool = True
    clip_target_q: float = 0.99
    test_size: float = 0.15
    val_size: float = 0.15
    random_state: int = 42
    n_iter: int = 4000
    depth: int = 8
    lr: float = 0.05
    early_stop: int = 200
