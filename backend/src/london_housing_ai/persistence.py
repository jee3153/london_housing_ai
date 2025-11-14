import os

import pandas as pd
from psycopg2.errors import UndefinedTable
from sqlalchemy import Engine, create_engine, text

from london_housing_ai.utils.logger import get_logger

logger = get_logger()

MAX_POSTGRES_IDENTIFIER_LENGTH = 63
TABLE_NAME_PREFIX = "london_housing_"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Environment variable '{name}' must be set for database connectivity."
        )
    return value


def get_engine() -> Engine:
    db_url = os.getenv("DB_CONNECTION_URL") or os.getenv("DB_CONN")
    if db_url:
        return create_engine(db_url)

    username = _require_env("DB_USERNAME")
    password = _require_env("DB_PASSWORD")
    host = _require_env("DB_HOST")
    port = _require_env("DB_PORT")
    db_name = _require_env("DB_NAME")
    return create_engine(f"postgresql://{username}:{password}@{host}:{port}/{db_name}")


def persist_dataset(df: pd.DataFrame, engine: Engine, checksum: str):
    if checksum is None:
        raise RuntimeError("checksum table name is not provided.")
    table_name = _table_name_from_checksum(checksum)
    try:
        df.to_sql(table_name, engine, index=False)
    except Exception:
        raise RuntimeError(f"failed to persist table {table_name} to db.")


def get_dataset_from_db(engine: Engine, checksum: str | None = None) -> pd.DataFrame:
    if checksum is None:
        raise RuntimeError(
            "checksum is not provided hence table name wouldn't be known."
        )

    table_name = _table_name_from_checksum(checksum)
    try:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", engine)
    except UndefinedTable as e:
        raise ValueError(
            "table doesn't exist but dataset is already seen."
            + "If you are ingesting the same csv again for development purpose,"
            + f"please remove your checksum record in 'dataset_hashes' table. Error: {e}"
        )


def _table_name_from_checksum(checksum: str) -> str:
    """Return a legal Postgres table name derived from the dataset checksum."""
    suffix_len = MAX_POSTGRES_IDENTIFIER_LENGTH - len(TABLE_NAME_PREFIX)
    if suffix_len <= 0:
        raise RuntimeError("Invalid table name prefix; exceeds PostgreSQL limit.")
    return f"{TABLE_NAME_PREFIX}{checksum[:suffix_len]}"


def ensure_checksum_table(engine: Engine) -> None:
    stmt = text(
        """
    CREATE TABLE IF NOT EXISTS dataset_hashes (
        hash CHAR(64) PRIMARY KEY,
        table_name TEXT,
        inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    with engine.begin() as conn:
        conn.execute(stmt)


def dataset_already_persisted(engine: Engine, checksum: str) -> bool:
    sql = "SELECT 1 FROM dataset_hashes WHERE hash = :h LIMIT 1"
    with engine.begin() as conn:
        return conn.execute(text(sql), {"h": checksum}).first() is not None


def record_checksum(engine: Engine, checksum: str) -> None:
    table_name = _table_name_from_checksum(checksum)
    sql = """
        INSERT INTO dataset_hashes(hash, table_name)
        VALUES (:h, :t)
        ON CONFLICT (hash) DO UPDATE SET table_name = EXCLUDED.table_name
    """
    with engine.begin() as conn:
        conn.execute(text(sql), {"h": checksum, "t": table_name})


def reset_postgres(engine: Engine):
    recreate = """
        CREATE TABLE IF NOT EXISTS dataset_hashes (
            hash TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.execute(text(recreate))

    logger.info("DEV_MODE is on, postgres is reset and recreated.")
