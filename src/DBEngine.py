from typing import Callable
from sqlalchemy import create_engine

class DBEngine:
    def get_engine(self):
        return create_engine("postgresql+psycopg2://postgres:password@localhost:5432/mypostgres")
