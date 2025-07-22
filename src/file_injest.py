from pathlib import Path
from typing import List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def write_csv_to_partitioned_parquet(
    csv_path: Path,
    out_dir: Path,
    partition_cols: List[str],
    chunksize: int = 1_000_000,
    tmp_name: str = "tmp.parquet",
    compression: str = "snappy",
) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_table_path = out_dir / tmp_name

    parquet_writer = None
    for chunk in pd.read_csv(csv_path, chunksize=chunksize):
        table = pa.Table.from_pandas(chunk)
        if parquet_writer is None:
            parquet_writer = pq.ParquetWriter(
                where=temp_table_path, schema=table.schema, compression=compression
            )
        parquet_writer.write_table(table)
    if parquet_writer is not None:
        parquet_writer.close()

    # repartition into year folders
    pq.write_to_dataset(
        table=pq.read_table(temp_table_path),  # read table file at temp_table_path
        root_path=str(out_dir),
        partition_cols=partition_cols,  # partition by partition columns
    )

    temp_table_path.unlink()
