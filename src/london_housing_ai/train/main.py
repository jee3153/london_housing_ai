# from trainer.ModelTrainer import ModelTrainer
# from dbsetup import get_engine
# import argparse
# from pathlib import Path
# from typing import Dict, Any
# from loaders import load_dataset, load_cleaning_config, load_augment_config
# from pipeline import build_dataset
# from augmenters import add_floor_area


# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--config", type=str)
#     parser.add_argument("--csv", type=str)
#     parser.add_argument("--aug", type=str)
#     args = parser.parse_args()

#     root_path = Path(__file__).resolve().parent.parent
#     print(f"root path: {root_path}")
#     config_path = f"{root_path}/configs/{args.config}"
#     csv_path = f"{root_path}/data/{args.csv}"

#     cleaning_config = load_cleaning_config(config_path)
#     print(f"cleaning config path: {config_path} loaded")

#     df = load_dataset(csv_path, cleaning_config.col_headers, cleaning_config.required_cols)
#     df = build_dataset(df, cleaning_config)

#     aug_config = load_augment_config(config_path)
#     if aug_config:
#         if not args.aug:
#             raise RuntimeError(f"aug_config is prrovided but argument for augmented csv file path (--aug) is not provided.")
#         aug_csv_path = f"{root_path}/data/{args.aug}"

#         aug_df = load_dataset(aug_csv_path, aug_config.col_headers, aug_config.required_cols)
#         df = add_floor_area(
#             main_df=df,
#             aug_df=aug_df,
#             floor_col=aug_config.floor_col,
#             merge_key=aug_config.postcode_col,
#             how=aug_config.join_method,
#             min_match_rate=aug_config.min_match_rate
#         )

#     engine = get_engine()

#     # data_cleaner = DataCleaner(engine, config)
#     # loader = CSVLoader(engine, data_cleaner)
#     # loader.load_and_persist_csv(csv_path)

#     # today = datetime.date.fromtimestamp(time.time())
#     # table_name = data_cleaner.table_name_from_date(today.isoformat())

#     # df = loader.load_data_from_db(table_name)
#     # trainer = ModelTrainer(df)
#     # trainer.train()

# if __name__ == "__main__":
#     main()
