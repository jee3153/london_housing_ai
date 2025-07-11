from trainer.ModelTrainer import ModelTrainer
from DBEngine import DBEngine
from cleaner.DataCleaner import DataCleaner
from loader.CSVLoader import CSVLoader
import argparse
from pathlib import Path
from typing import Dict, Any
import yaml
import datetime
import time


def load_config(path: str) -> Dict[Any, Any]:
    with open(path) as f:
        return yaml.safe_load(f)
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument("--csv", type=str)
    args = parser.parse_args()
    root_path = Path(__file__).resolve().parent.parent
    print(f"root path: {root_path}")

    config_path = f"{root_path}/configs/{args.config}"
    csv_path = f"{root_path}/data/{args.csv}"

    config = dict(load_config(config_path))
    print(f"config path: {config_path} loaded")

    engine = DBEngine()
    data_cleaner = DataCleaner(engine, config)
    loader = CSVLoader(engine, data_cleaner)
    loader.load_and_persist_csv(csv_path)

    # today = datetime.date.fromtimestamp(time.time())
    # table_name = data_cleaner.table_name_from_date(today.isoformat())

    # df = loader.load_data_from_db(table_name)
    # trainer = ModelTrainer(df)
    # trainer.train()

if __name__ == "__main__":
    main()    