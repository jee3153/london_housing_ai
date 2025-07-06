from os import path
from loader.CSVLoader import CSVLoader
import mlflow
from mlflow.tracking import MlflowClient
from pprint import pprint
from DBEngine import DBEngine
from cleaner.DataCleaner import DataCleaner
from trainer.ModelTrainer import ModelTrainer

def main() -> None:
    tracking_uri = "http://localhost:5000"
    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient(tracking_uri=tracking_uri)

    cur_dir = path.dirname(path.abspath(__file__))
    csv_path = path.normpath(path.join(cur_dir, "..", "data", "london.csv")) 
    engine = DBEngine()
    loader = CSVLoader(engine, DataCleaner(engine))
    
    # df = loader.load_from_csv(csv_path)
    df = loader.load_data_from_db("london_housing_2025_07_05")
    trainer = ModelTrainer(df)
    trainer.train()

    print(df.head())
    print(client.search_experiments())

    
if __name__ == "__main__":
    main()    