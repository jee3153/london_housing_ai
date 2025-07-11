import pandas as pd
from pandas import DataFrame
import re
import requests
from typing import Dict, Any, List, Tuple
from DBEngine import DBEngine
import numpy as np
from numpy import ndarray
from pathlib import Path
from functools import reduce

class DataCleaner:
    def __init__(self, engine: DBEngine, config: Dict[Any, Any]):
        self.engine = engine
        self.config = config

    def convert_column_dtype(self, df: DataFrame, dtype_map: Dict[str, str]) -> DataFrame:
        for col, dtype in dtype_map.items():
            if dtype in ("integer", "float"):
                df[col] = pd.to_numeric(df[col], errors="coerce")   # ← keep it
            elif dtype == "datetime":
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df  

    def convert_to_sqft(self, df: DataFrame, area_column: str, config: Any) -> DataFrame:
        unit = self.deep_get(config, ["cleaning", "convert_to_sqft_from"])
        if unit == "m":
            df[area_column] = pd.to_numeric(df[area_column], errors="coerce")
            df["area_in_sqft"] = round(df[area_column] * 10.7639)
        return df    

    def normalise(self, original_df: DataFrame, aug_df: DataFrame) -> Tuple[DataFrame, DataFrame]:
        print(f"original_df: {original_df.columns}, aug_df: {aug_df.columns}")
        for df, col in zip((original_df, aug_df), ("postal_code", "POSTCODE")):
            df[col] = df[col].str.upper()
            df["outcode"] = df[col].str.extract(r"^([A-Z0-9]+)")
            df["incode"] = df[col].str.extract(r"([0-9][A-Z][A-Z])$")
            df["postcode_clean"] = (
                df[col]
                    .str.replace(" ", "")
                    .str.strip()
            ) 
        return original_df, aug_df 
    
    def canon_postcode(self, series):
        return (
        series.astype("string")               # guarantee string dtype
              .str.upper()                    # SW1A 1AA → SW1A 1AA
              .str.replace(r"\s+", "", regex=True)  # kill *every* space → SW1A1AA
              .str.strip()                    # trim lingering whitespace
    )
    """
    Supplement data with augmented data set
    """
    def merge_aug_data(self, df: DataFrame) -> DataFrame:
        config = self.config

        TOTAL_FLOOR_AREA = "TOTAL_FLOOR_AREA"
        AREA_IN_SQFT = "area_in_sqft"
        POSTCODE = "POSTCODE"
        CONVERT_TO_SQFT_FROM = "convert_to_sqft_from"
        CLEANING = "cleaning"
        column_map = config["aug_columns"]
        file_name = self.deep_get(config, ["feature_engineering", "file_name"])
        aug_file_path = f"{Path(__file__).resolve().parent.parent}/data/{file_name}"
        aug_dtype_map = config["aug_dtype"]
        aug_df = pd.read_csv(aug_file_path, usecols=column_map.keys(), dtype={col: dtype for col, dtype in aug_dtype_map.items() if dtype == "string"})

        if aug_dtype_map:
            aug_df = self.convert_column_dtype(aug_df, aug_dtype_map)

        if POSTCODE in column_map.keys():
            df, aug_df = self.normalise(df, aug_df)

        if TOTAL_FLOOR_AREA in column_map.keys() and self.deep_get(config, [CLEANING, CONVERT_TO_SQFT_FROM]):
            aug_df = self.convert_to_sqft(aug_df, TOTAL_FLOOR_AREA, config)

        del column_map["POSTCODE"]        
      
        if TOTAL_FLOOR_AREA not in df.columns:
            df[TOTAL_FLOOR_AREA] = pd.NA
     
        aug_df["TOTAL_FLOOR_AREA"] = pd.to_numeric(aug_df["TOTAL_FLOOR_AREA"], errors="coerce")

        agg_df = (
            aug_df.groupby("postcode_clean", as_index=False)
                .agg({"area_in_sqft": "median"})     # <- use the ft² column
        )
        df = df.drop(columns=[TOTAL_FLOOR_AREA], errors="ignore")

        merged_df = df.merge(agg_df, on="postcode_clean", how="left", validate="m:1")
        match_rate = merged_df["area_in_sqft"].notna().mean()

        print(f"Matched floor-area for {match_rate:.1%} of rows")
        
        return merged_df
     
    def deep_get(self, d: Dict, keys: List[str], default=None) -> Any:
        """
        Traverse a nested dict (d) following `keys`
        (`keys` is an iterable like ('a', 'b', 'c')).
        If any key is missing, return `default`.
        """
        current = d
        for k in keys:
            try:
                current = current[k]   
            except (KeyError, IndexError, TypeError):
                return default
        return current
        
    def clean_data(self, df:DataFrame) -> DataFrame:
        config = self.config

        df.duplicated()
        missing_column_titles = self.deep_get(config, ["cleaning", "missing_columns"])
           
        if missing_column_titles:
            if len(df.columns) != len(missing_column_titles):
                raise RuntimeError(f"column length of df is not matching with configured column length.")
            df.columns = missing_column_titles

        df = df.rename(columns=config["column_mapping"])    

        if self.deep_get(config, ["cleaning", "drop_na"], default=None):
            df = df.dropna()
        if self.deep_get(config, ["cleaning", "house_type_lower"]):
            df.loc[:, "house_type"] = df["house_type"].str.lower()    
        if self.deep_get(config, ["cleaning", "filter_county"]):
            london_mask = df["county"].str.contains("london", case=False, na=False)
            df = df[london_mask]  
        if self.deep_get(config, ["cleaning", "handle_skew"]):
            df.loc[:, "price"] = df["price"].clip(upper=df["price"].quantile(0.99))      
        # if self.deep_get(config, ["feature_engineering", "map_postcode_to_district"]):    
        #     df = self.map_postcodes_to_locations(df, "postal_code", "location")
        if self.deep_get(config, ["feature_engineering", "file_name"]):
            df = self.merge_aug_data(df)

        # print(f"required columns: {config["required_columns"]}")
        # df = df[config["required_columns"]]
        # df = self.merge_house_types(df, self.deep_get(config, ["feature_engineering", "house_type"]))

        # df = self.drop_niche_categories(df, "location", self.deep_get(config, ["feature_engineering", "location", "larger_or_equal_to"]))
        # today = datetime.date.fromtimestamp(time.time())
        # table_name = self.table_name_from_date(today.isoformat())
        # engine = self.engine.get_engine()

        # try:
        #     df.to_sql(table_name, engine, if_exists="fail", index=False)
        # except:
        #     print(f"not storing data to {table_name} since it already exists.")    
        
        return df
    
    def table_name_from_date(self, iso_format: str) -> str:
        date = re.sub(r"-", "_", iso_format)
        return f"london_housing_{date}" 

    def drop_columns(self, df: DataFrame, *kargs: str) -> DataFrame:
        return df.drop([*kargs], axis=1)

        
    def build_map_postcode_location(self, postcodes: ndarray, failed_queries: List[str]) -> Dict[Any, Any]:
        url = "https://api.postcodes.io/postcodes"
        headers = {"Content-Type": "application/json"}
        payload = {"postcodes": list(postcodes)}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()["result"]
            locations = {}
            for result in data:
                postcode = result["query"]
                if "result" not in result:
                    continue

                result_for_each = result["result"]
                if not result_for_each:
                    print(f"query for {postcode} is not found.")
                    failed_queries.append(postcode)
                    continue
                
                if "admin_district" not in result_for_each:
                    continue
                locations[postcode] = result_for_each['admin_district']
           
            return locations
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return {postcode: np.nan for postcode in postcodes}
            
    """
    Fill in locations based on postcode, to get consistent categories for locations
    """
    def map_postcodes_to_locations(self, df:DataFrame, column_name:str, new_column_name:str) -> DataFrame:
        unique_postcodes = df[column_name].unique()
        batch_size = 100
        failed_queries = []
        postcode_location_map = {}

        for i in range(0, len(unique_postcodes), batch_size):
            batch = unique_postcodes[i:i + batch_size]
            postcode_location_map.update(self.build_map_postcode_location(batch, failed_queries))

        self.handle_failed_postcodes(df, failed_queries)
        df.loc[:, new_column_name] = df.loc[:, column_name].map(postcode_location_map)
        return df
    
    def handle_failed_postcodes(self, df: DataFrame, failed_queries: List[str]) -> DataFrame:
        return df.loc[~df["postal_code"].isin(failed_queries), :]

    def prepare_locations(self, df: DataFrame) -> DataFrame:
        niche, top3 = self.find_niche_categories(df, "house_type")
        majour_to_niche = {column: [] for column in top3}
        for column in niche: 
            if column == "Studio":
                majour_to_niche["Flat / Apartment"].append(column)
            elif column in ["Bungalow", "Duplex", "Mews"]:
                majour_to_niche["House"].append(column)
            else:
                majour_to_niche["New development"].append(column)

        return self.merge_house_types(df, majour_to_niche)

    """
    Filters values of column that are >= configured count
    """
    def drop_niche_categories(self, df: DataFrame, col_name: str, count: int) -> DataFrame:
        return df[df[col_name].map(df[col_name].value_counts()) >= 10]


    def find_niche_categories(self, df: DataFrame, col_name: str) -> tuple[set, set]:
        column = df[col_name]
        top3 = set(column.value_counts().nlargest(3).index)
        all_categories = set(column.unique())
        return (all_categories - top3, top3)
       
    def merge_house_types(self, df: DataFrame, merge_map: Dict[str, List[str]]) -> DataFrame:
        updated_df = df
        for merge_to, merge_froms in merge_map.items():
            updated_df = df.replace(merge_froms, merge_to)
        return updated_df 
