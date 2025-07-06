from trainer.ModelTrainer import ModelTrainer
from DBEngine import DBEngine
from cleaner.DataCleaner import DataCleaner
from loader.CSVLoader import CSVLoader
import datetime
import time


def main():
    engine = DBEngine()
    data_cleaner = DataCleaner(engine)
    loader = CSVLoader(engine, data_cleaner)

    today = datetime.date.fromtimestamp(time.time())
    table_name = data_cleaner.table_name_from_date(today.isoformat())

    df = loader.load_data_from_db(table_name)
    trainer = ModelTrainer(df)
    trainer.train()

if __name__ == "__main__":
    main()    