import datetime
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest
from sqlalchemy import MetaData
from testcontainers.postgres import PostgresContainer

from london_housing_ai.persistence import _get_table_name_from_date, get_engine


@pytest.fixture(scope="module", autouse=True)
def mlflow_uri(tmp_path_factory):
    mlruns_dir = tmp_path_factory.mktemp("mlruns")
    os.environ["MLFLOW_TRACKING_URI"] = f"file://{mlruns_dir}"


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


def test_train_main_e2e(request: pytest.FixtureRequest):

    root = Path(request.config.rootpath)
    config_file = (
        root / "src" / "london_housing_ai" / "configs" / "config_dataset2.yaml"
    )
    csv_file = root / "tests" / "fixtures" / "sample_housing.csv"

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
    )

    assert result.returncode == 0, f"Train pipeline failed:\n{result.stderr}"
    assert "the experiment of model has completed." in result.stdout
