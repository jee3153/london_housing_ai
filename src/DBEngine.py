from sqlalchemy import create_engine
import os

class DBEngine:
    def get_engine(self):
        db_name = "postgres" if os.environ["MODE"] == "PROD" else "mypostgres"
        host = "postgres" if os.environ["MODE"] == "PROD" else "localhost"
        return create_engine(f"postgresql://postgres:password@{host}:5432/{db_name}")
