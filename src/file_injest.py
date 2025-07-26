from pathlib import Path
from typing import List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


from pathlib import Path
from typing import List
from google.cloud import storage

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import json


def write_df_to_partitioned_parquet(
    df: pd.DataFrame,
    out_dir: Path,
    partition_cols: List[str],
) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pandas(df)

    # repartition into year folders
    pq.write_to_dataset(
        table=table,  # read table file at temp_table_path
        root_path=str(out_dir),
        partition_cols=partition_cols,  # partition by partition columns
    )


def upload_parquet_to_gcs(
    local_dir: Path,
    bucket_name: str,
    destination_blob_name: str,
    credential_path: str | None,
) -> None:
    if not credential_path:
        raise ValueError("credential_path is not provided.")

    credential_json = None
    with open(credential_path) as f:
        credential_json = json.load(f)

    storage_client = storage.Client(project=credential_json["project_id"])
    bucket = storage_client.bucket(bucket_name)

    for local_file_path in local_dir.rglob("*.parquet"):
        blob_name = f"{destination_blob_name}/{local_file_path.relative_to(local_dir)}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_file_path))
        print(f"Uploaded {local_file_path} to gs://{bucket_name}/{blob_name}")
