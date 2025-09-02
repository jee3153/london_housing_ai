from sqlalchemy import create_engine, Engine, text, inspect
from typing import List
import os
import pandas as pd
import datetime
import time
import re
from psycopg2.errors import UndefinedTable
import ray


def get_engine() -> Engine:
    db_name = "postgres" if os.environ["MODE"] == "PROD" else "mypostgres"
    host = "postgres" if os.environ["MODE"] == "PROD" else "localhost"
    return create_engine(f"postgresql://postgres:password@{host}:5432/{db_name}")


def persist_dataset(df: pd.DataFrame, engine: Engine, table_name: str | None = None):
    if table_name == None:
        table_name = _get_table_name_from_date(
            datetime.date.fromtimestamp(time.time()).isoformat()
        )
    try:
        df.to_sql(table_name, engine, index=False)
    except Exception as e:
        raise RuntimeError(f"failed to persist table {table_name} to db.")


def get_dataset_from_db(engine, table_name: str | None = None) -> ray.data.Dataset:
    if table_name == None:
        table_name = _get_table_name_from_date(
            datetime.date.fromtimestamp(time.time()).isoformat()
        )
    try:
        return ray.data.read_sql(f"SELECT * FROM {table_name}", engine)
    except UndefinedTable as e:
        raise ValueError(
            f"table doesn't exist but dataset is already seen."
            + "If you are ingesting the same csv again for development purpose,"
            + "please remove your checksum record in 'dataset_hashes' table. Error: {e}"
        )


def _get_table_name_from_date(today_iso: str) -> str:
    date = re.sub(r"-", "_", today_iso)
    return f"london_housing_{date}"


def ensure_checksum_table(engine: Engine) -> None:
    stmt = """
    CREATE TABLE IF NOT EXISTS dataset_hashes (
        hash CHAR(64) PRIMARY KEY,
        table_name TEXT,
        inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def dataset_already_persisted(engine: Engine, checksum: str) -> bool:
    sql = "SELECT 1 FROM dataset_hashes WHERE hash = :h LIMIT 1"
    with engine.begin() as conn:
        return conn.execute(text(sql), {"h": checksum}).first() is not None


def record_checksum(
    engine: Engine,
    checksum: str,
    table_name: str = _get_table_name_from_date(
        datetime.date.fromtimestamp(time.time()).isoformat()
    ),
) -> None:
    sql = """
        INSERT INTO dataset_hashes(hash, table_name)
        VALUES (:h, :t)
        ON CONFLICT (hash) DO NOTHING
    """
    with engine.begin() as conn:
        conn.execute(text(sql), {"h": checksum, "t": table_name})


def table_exists(engine: Engine, table_name: str) -> bool:
    inspector = inspect(engine)
    return inspector.has_table(table_name)
