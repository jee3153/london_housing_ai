import mlflow
import argparse
import asyncio
import datetime
import time
import re

from argparse import Namespace
from pathlib import Path
from src.loaders import (
    load_dataset,
    load_cleaning_config,
    load_augment_config,
    load_train_config,
    load_fe_config,
    load_parquet_config,
)
from src.pipeline import (
    clean_dataset,
    feature_engineer_dataset,
    df_with_required_cols,
)
from augmenters import add_floor_area
from models import PriceModel
from persistence import (
    persist_dataset,
    get_engine,
    get_dataset_from_db,
    ensure_checksum_table,
    dataset_already_persisted,
    record_checksum,
    _get_table_name_from_date,
    table_exists,
)
from file_injest import write_df_to_partitioned_parquet, upload_parquet_to_gcs
from utils.checksum import file_sha256
from dotenv import load_dotenv
import os

load_dotenv()


def main(args: Namespace) -> None:

    if not args.config or not args.csv:
        raise ValueError(
            f"Argument value for config and csv are required. config='{args.config}', csv='{args.csv}'"
        )

    mlflow.set_tracking_uri("http://mlflow:5000")
    print("Current tracking URI is:", mlflow.get_tracking_uri())

    root_path = Path(__file__).resolve().parent  # /app
    config_path = root_path / "configs" / args.config
    csv_path = root_path / "data" / args.csv
    data_path = root_path / "data_lake"

    engine = get_engine()
    ensure_checksum_table(engine)
    checksum = file_sha256(csv_path)
    table_name = _get_table_name_from_date(
        datetime.date.fromtimestamp(time.time()).isoformat()
    )
    # if dataset exists load dataset from db
    if dataset_already_persisted(engine, checksum) or table_exists(engine, table_name):
        print(
            f"checksum '{checksum}' for '{csv_path}' is found, skipping cleaning and extraction."
        )
        df = get_dataset_from_db(engine, table_name)
    else:
        print(
            f"checksum '{checksum}' for '{csv_path}' is not found, proceeding cleaning and extraction."
        )

        # if dataset not exist, proceed cleaning and data extraction
        cleaning_config = load_cleaning_config(config_path)
        df = load_dataset(
            csv_path, cleaning_config.col_headers, cleaning_config.loading_cols
        )
        df = clean_dataset(df, cleaning_config)

        # ------comment it only when gcs uploading is required.
        # silver layer check-point
        # parquet_config = load_parquet_config(config_path)
        # parquet_dir = data_path / "silver"

        # write_df_to_partitioned_parquet(
        #     df=df,
        #     out_dir=parquet_dir,
        #     partition_cols=parquet_config.silver_partition_cols,
        # )
        # upload_parquet_to_gcs(
        #     local_dir=parquet_dir,
        #     bucket_name=parquet_config.bucket_name,
        #     destination_blob_name=parquet_config.destination_blob_name,
        #     credential_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        #     cleanup=args.cleanup_local,
        # )

        df = asyncio.run(
            feature_engineer_dataset(
                df, load_fe_config(config_path), cleaning_config.postcode_col
            )
        )
        # merging with supplement dataset
        if args.aug:
            aug_config = load_augment_config(config_path)
            if aug_config is None:
                raise ValueError(
                    "Augment config could not be loaded. Please check your config file."
                )
            aug_csv_path = root_path / "data" / args.aug
            aug_df = load_dataset(
                aug_csv_path, aug_config.col_headers, aug_config.required_cols
            )
            df = add_floor_area(
                main_df=df,
                aug_df=aug_df,
                floor_col=aug_config.floor_col,
                merge_key=aug_config.postcode_col,
                how=aug_config.join_method,
                min_match_rate=aug_config.min_match_rate,
            )

        # gold layer check-point

        # persist clean/merged dataset
        persist_dataset(df, engine, table_name)
        record_checksum(engine, checksum, table_name)

    # model training
    with mlflow.start_run(run_name="catboost_baseline"):
        train_cfg = load_train_config(config_path)
        trainer = PriceModel(train_cfg)
        trainer.fit(df_with_required_cols(df, train_cfg), checksum)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument("--csv", type=str)
    parser.add_argument("--aug", type=str)
    parser.add_argument("--cleanup_local", action="store_true")
    args = parser.parse_args()
    main(args)
