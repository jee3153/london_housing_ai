import argparse
import asyncio
import os
from argparse import Namespace

import mlflow
import mlflow.catboost as mlflow_catboost
import mlflow.exceptions
from dotenv import load_dotenv
from mlflow import MlflowClient

from london_housing_ai.augmenters import add_floor_area
from london_housing_ai.experiment_logger import ExperimentLogger
from london_housing_ai.file_injest import (
    upload_parquet_to_gcs,
    write_df_to_partitioned_parquet,
)
from london_housing_ai.loaders import (
    load_augment_config,
    load_cleaning_config,
    load_dataset,
    load_fe_config,
    load_parquet_config,
    load_train_config,
)
from london_housing_ai.models import PriceModel
from london_housing_ai.persistence import (
    dataset_already_persisted,
    ensure_checksum_table,
    get_dataset_from_db,
    get_engine,
    persist_dataset,
    record_checksum,
    reset_postgres,
)
from london_housing_ai.pipeline import (
    clean_dataset,
    df_with_required_cols,
    feature_engineer_dataset,
)
from london_housing_ai.utils.checksum import file_sha256
from london_housing_ai.utils.logger import get_logger
from london_housing_ai.utils.paths import get_project_root

load_dotenv()
logger = get_logger()


def main(args: Namespace) -> None:  # noqa: C901
    if not args.config or not args.csv:
        raise ValueError(
            f"Argument value for config and csv are required. config='{args.config}', csv='{args.csv}'"
        )
    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    logger.info(f"Current tracking URI is: {mlflow.get_tracking_uri()}")

    root_path = get_project_root()  # /app
    config_path = root_path / args.config
    csv_path = root_path / args.csv
    data_path = root_path / "data_lake"

    engine = get_engine()
    ensure_checksum_table(engine)
    checksum = file_sha256(csv_path)

    # if dataset exists load dataset from db
    if dataset_already_persisted(engine, checksum):
        logger.info(
            f"checksum '{checksum}' for '{csv_path}' is found, skipping cleaning and extraction."
        )
        df = get_dataset_from_db(engine, checksum)
    else:
        logger.info(
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
        parquet_config = load_parquet_config(config_path)
        parquet_dir = data_path / "silver"

        write_df_to_partitioned_parquet(
            df=df,
            out_dir=parquet_dir,
            partition_cols=parquet_config.silver_partition_cols,
        )
        upload_parquet_to_gcs(
            local_dir=parquet_dir,
            destination_blob_name=parquet_config.destination_blob_name,
            credential_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
            cleanup=args.cleanup_local,
        )
        # -------end of gcs uploading

        df = asyncio.run(
            feature_engineer_dataset(
                df, load_fe_config(config_path), cleaning_config.postcode_col
            )
        )
        if df.empty:
            return
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
        persist_dataset(df, engine, checksum)
        record_checksum(engine, checksum)

    # model training
    client = MlflowClient()
    EXPERIMENT_NAME = "LondonHousingAI"
    artifact_location = os.getenv("MLFLOW_ARTIFACT_URI", "file:/mlruns")
    try:
        client.create_experiment(EXPERIMENT_NAME, artifact_location=artifact_location)
    except mlflow.exceptions.RestException:
        logger.info(
            f"The experiment {EXPERIMENT_NAME} already exists. Skip creating experiment."
        )

    mlflow.set_experiment(experiment_name=EXPERIMENT_NAME)

    # start logging metadata as you train a model
    with mlflow.start_run(run_name="london_housing_run") as run:
        train_cfg = load_train_config(config_path)
        training_df = df_with_required_cols(df, train_cfg)
        trainer = PriceModel(train_cfg)
        trainer.train_and_evaluate(training_df, checksum)

        try:
            # log trained model into MLflow under consistent path
            mlflow_catboost.log_model(
                cb_model=trainer.model,
                artifact_path=os.getenv("MLFLOW_ARTIFACT_PATH", "catboost_model"),
                input_example=training_df.iloc[:1],
            )
        except Exception as exc:
            logger.exception(
                f"Failed to log Catboost model to MLflow. caused by: {exc}"
            )
            raise
        experiment_logger = ExperimentLogger(trainer, run)
        experiment_logger.log_all()
        logger.info(f"the experiment of model has completed. run_id={run.info.run_id}")

    if os.getenv("DEV_MODE", "false") == "true":
        reset_postgres(engine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument("--csv", type=str)
    parser.add_argument("--aug", type=str)
    parser.add_argument("--cleanup_local", action="store_true")
    args = parser.parse_args()
    main(args)
