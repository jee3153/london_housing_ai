import mlflow
import argparse
from argparse import Namespace
from pathlib import Path
from loaders import (
    load_dataset, 
    load_cleaning_config, 
    load_augment_config, 
    load_train_config, 
    load_fe_config,
    load_parquet_config
)
from pipeline import (
    clean_dataset, 
    feature_engineer_dataset, 
    df_with_required_cols,
    add_sold_year_column
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
    write_in_chunks
)
from utils.checksum import file_sha256
import asyncio


def main(args: Namespace) -> None:
    mlflow.set_tracking_uri("http://mlflow:5000")
    print("Current tracking URI is:", mlflow.get_tracking_uri())

    root_path   = Path(__file__).resolve().parent      # /app
    config_path = root_path / "configs" / args.config
    csv_path    = root_path / "data"    / args.csv
    data_path   = root_path / "data_lake"


    
    cleaning_config = load_cleaning_config(config_path)
    df = load_dataset(csv_path, cleaning_config.col_headers, cleaning_config.required_cols)
    df = clean_dataset(df, cleaning_config)
    

    # silver layer check-point
    parquet_config = load_parquet_config(config_path)
    df = add_sold_year_column(df, parquet_config.sold_timestamp_col)
    write_in_chunks(csv_path, data_path / "silver", parquet_config.silver_partition_cols)

    df = asyncio.run(feature_engineer_dataset(df, load_fe_config(config_path), cleaning_config.postcode_col)) 
    # merging with supplement dataset
    if args.aug: 
        aug_config = load_augment_config(config_path)
        if aug_config is None:
            raise ValueError("Augment config could not be loaded. Please check your config file.")
        aug_csv_path = root_path / "data" / args.aug
        aug_df       = load_dataset(aug_csv_path, aug_config.col_headers, aug_config.required_cols)
        df = add_floor_area(
            main_df=df, 
            aug_df=aug_df, 
            floor_col=aug_config.floor_col,
            merge_key=aug_config.postcode_col,
            how=aug_config.join_method,
            min_match_rate=aug_config.min_match_rate
        )

    # gold layer check-point
    
    engine = get_engine()
    ensure_checksum_table(engine)
    checksum = file_sha256(csv_path)

    if not dataset_already_persisted(engine, checksum):
        # persist clean/merged dataset
        persist_dataset(df, engine)
        record_checksum(engine, checksum)

    # load dataset from db
    df = get_dataset_from_db(engine)

    # model training
    with mlflow.start_run(run_name="catboost_baseline"):
        train_cfg = load_train_config(config_path)
        trainer = PriceModel(train_cfg)
        trainer.fit(df_with_required_cols(df, train_cfg))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument("--csv", type=str)
    parser.add_argument("--aug", type=str)
    args = parser.parse_args()
    main(args)    