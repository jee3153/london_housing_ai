import pandas as pd
from typing import Any
from pandas import DataFrame
from DBEngine import DBEngine
from cleaner.DataCleaner import DataCleaner


class CSVLoader:   
    def __init__(self, engine: DBEngine, data_cleaner: DataCleaner):
        self.engine = engine
        self.cleaner = data_cleaner
        
    def load_and_persist_csv(self, csv_path: str) -> DataFrame:   
        df: DataFrame = pd.read_csv(csv_path)
        print(f"file {csv_path} is loaded.")
        return self.cleaner.clean_data(df)
    
    def load_data_from_db(self, table_name: str) -> DataFrame:
        engine = self.engine.get_engine()
        return pd.read_sql_query(f"SELECT * FROM {table_name}", engine)

    
