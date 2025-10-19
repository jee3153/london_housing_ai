import json
import os
import shutil
from pathlib import Path
from typing import List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import storage
from london_housing_ai.utils.logger import get_logger

logger = get_logger()


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
    cleanup: bool,
) -> None:
    if not credential_path:
        raise ValueError("credential_path is not provided.")

    storage_client = get_storage_client(credential_path)
    bucket = storage_client.bucket(bucket_name)

    for local_file_path in local_dir.rglob("*.parquet"):
        blob_name = f"{destination_blob_name}/{local_file_path.relative_to(local_dir)}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_file_path))

        logger.info(f"Uploaded {local_file_path} to gs://{bucket_name}/{blob_name}")

    if cleanup:
        _cleanup_local_parquets(local_dir)


def get_storage_client(credential_path: str) -> storage.Client:
    if not credential_path:
        raise ValueError("credential_path is not provided.")

    credential_json = None
    with open(credential_path) as f:
        credential_json = json.load(f)

    return storage.Client(project=credential_json["project_id"])


def _cleanup_local_parquets(dir_path: Path):
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
    else:
        os.remove(dir_path)
