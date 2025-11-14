import os
import shutil
import subprocess
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import MetaData
from testcontainers.postgres import PostgresContainer

from london_housing_ai.persistence import get_engine
from london_housing_ai.train_main import main


@pytest.fixture(scope="module", autouse=True)
def mlflow_uri(tmp_path_factory):
    tracking_dir = tmp_path_factory.mktemp("mlruns")
    artifacts_dir = tmp_path_factory.mktemp("mlartifacts")
    os.environ["MLFLOW_TRACKING_URI"] = f"file://{tracking_dir}"
    os.environ["MLFLOW_ARTIFACT_URI"] = f"file://{artifacts_dir}"


postgres = PostgresContainer("postgres:16-alpine")


@pytest.fixture(scope="module", autouse=True)
def db_connection(request: pytest.FixtureRequest):
    postgres.start()

    def remove_container():
        postgres.stop()

    # register teardown
    request.addfinalizer(remove_container)

    os.environ["DB_CONN"] = postgres.get_connection_url()
    os.environ["DB_HOST"] = postgres.get_container_host_ip()
    os.environ["DB_PORT"] = str(postgres.get_exposed_port(5432))
    os.environ["DB_USERNAME"] = postgres.username
    os.environ["DB_PASSWORD"] = postgres.password
    os.environ["DB_NAME"] = postgres.dbname


@pytest.fixture(scope="function", autouse=True)
def cleanup(request: pytest.FixtureRequest):
    if not os.getenv("DB_CONN"):
        raise ConnectionError("cannot connect to db since db url is none.")

    # --- Database cleanup ---
    engine = get_engine()
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)

    # --- File cleanup (after test) ---
    def remove_data_lake():
        root = Path(request.config.rootpath)
        data_lake_dir = root / "src" / "london_housing_ai" / "data_lake"
        for p in data_lake_dir.glob("*"):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p)
        print(f"✅ Removed data_lake directory: {data_lake_dir}")

    request.addfinalizer(remove_data_lake)


@pytest.mark.gcs
def test_train_main_e2e(request: pytest.FixtureRequest):
    root = Path(request.config.rootpath)
    config_file = (
        root / "src" / "london_housing_ai" / "configs" / "config_dataset2.yaml"
    )
    csv_file = root / "tests" / "fixtures" / "sample_housing.csv"

    env = os.environ
    env["PYTHONPATH"] = str(Path(request.config.rootpath) / "src")

    result = subprocess.run(
        [
            "python",
            "-m",
            "london_housing_ai.train_main",
            "--config",
            config_file,
            "--csv",
            csv_file,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )

    assert result.returncode == 0, f"Train pipeline failed:\n{result.stderr}"
    assert "the experiment of model has completed." in result.stdout


def test_train_main_e2e_local(request: pytest.FixtureRequest, caplog):
    # Skip real GCS upload
    with patch("london_housing_ai.train_main.upload_parquet_to_gcs") as mock_upload:
        mock_upload.return_value = None

        root = Path(request.config.rootpath)
        config_file = (
            root / "src" / "london_housing_ai" / "configs" / "config_dataset2.yaml"
        )
        csv_file = root / "tests" / "fixtures" / "sample_housing.csv"

        # env = os.environ
        # env["PYTHONPATH"] = str(Path(request.config.rootpath) / "src")
        args = Namespace(
            config=str(config_file),
            csv=str(csv_file),
            aug=None,
            cleanup_local=False,
        )
        main(args)
    assert "the experiment of model has completed." in caplog.text
    # now run the real training entry point
    # result = subprocess.run(
    #     [
    #         "python",
    #         "-m",
    #         "london_housing_ai.train_main",
    #         "--config",
    #         config_file,
    #         "--csv",
    #         csv_file,
    #     ],
    #     capture_output=True,
    #     text=True,
    #     timeout=120,
    #     env=env,
    # )

    # assert result.returncode == 0
    # assert "the experiment of model has completed." in result.stdout
