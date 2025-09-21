from typing import Callable, overload
import pandas as pd
import numpy as np

class Dataset:
    @overload
    def map_batches(
        self,
        fn: Callable[[pd.DataFrame], pd.DataFrame],
        *,
        batch_format: str = "pandas"
    ) -> "Dataset": ...
    @overload
    def map_batches(
        self, fn: Callable[[dict], dict], *, batch_format: str = "default"
    ) -> "Dataset": ...
    @overload
    def map_batches(
        self, fn: Callable[[np.ndarray], np.ndarray], *, batch_format: str = "numpy"
    ) -> "Dataset": ...
