from ray.data.aggregate import AggregateFnV2
from typing import List, Optional, Any
from ray.data.block import Block, BlockAccessor
import numpy as np


class Median(AggregateFnV2):
    def __init__(
        self,
        on: Optional[str] = None,
        ignore_nulls: bool = True,
        alias_name: Optional[str] = None,
    ):
        super().__init__(
            alias_name if alias_name else f"median({str(on)})",
            on=on,
            ignore_nulls=ignore_nulls,
            # NOTE: We've to copy returned list here, as some
            #       aggregations might be modifying elements in-place
            zero_factory=lambda: [],  # noqa: C410
        )

    def aggregate_block(self, block: Block) -> List:
        accessor = BlockAccessor.for_block(block)
        col = accessor.to_pandas()[self._target_col_name].dropna().tolist()
        return col

    def combine(self, current_accumulator: List, new: List) -> Any:
        return list(current_accumulator) + list(new)

    def finalize(self, accumulator: List[float]) -> float | None:
        if not accumulator:
            return None
        return float(np.median(accumulator))
