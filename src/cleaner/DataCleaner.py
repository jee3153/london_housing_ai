from pandas import DataFrame
import re
import datetime
import time
import requests
from typing import Dict, Any, List
from DBEngine import DBEngine
import numpy as np
from numpy import ndarray

class DataCleaner:
    def __init__(self, engine: DBEngine):
        self.engine = engine

    def clean_data(self, df:DataFrame) -> DataFrame:
        df = self.drop_columns(df, "Unnamed: 0", "Property Name", "No. of Receptions", "No. of Bathrooms", "Location", "City/County")
        df = df.dropna(subset=["Price", "Area in sq ft", "No. of Bedrooms", "Postal Code"])
        df = self.map_postcodes_to_locations(df, "Postal Code", "location")
        col_rename_map = {
            "House Type": "house_type", 
            "Area in sq ft": "area_in_sqft",
            "No. of Bedrooms": "no_bedrooms",
            "Location": "location",
            "Price": "price"
        }
        df = self.convert_column_names(df, col_rename_map)
        df = self.prepare_house_types(df)
        df = self.drop_niche_categories(df, "location")
        today = datetime.date.fromtimestamp(time.time())
        table_name = self.table_name_from_date(today.isoformat())
        engine = self.engine.get_engine()
        
        try:
            df.to_sql(table_name, engine, if_exists="fail", index=False)
        except:
            print(f"not storing data to {table_name} since it already exists.")    
        
        return df
    
    def table_name_from_date(self, iso_format: str) -> str:
        date = re.sub(r"-", "_", iso_format)
        return f"london_housing_{date}" 

    def drop_columns(self, df: DataFrame, *kargs: str) -> DataFrame:
        return df.drop([*kargs], axis=1)

    def convert_column_names(self, df: DataFrame, map_to_from: Dict[str, str]) -> DataFrame:
        return df.rename(columns=map_to_from)
        
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
        # df[new_column_name] = df[column_name].map(postcode_location_map)
        return self.drop_columns(df, column_name)
    
    def handle_failed_postcodes(self, df: DataFrame, failed_queries: List[str]) -> DataFrame:
        return df.loc[~df["Postal Code"].isin(failed_queries), :]
    
    def prepare_house_types(self, df: DataFrame) -> DataFrame:
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
    Filters values of column that are >= 10
    """
    def drop_niche_categories(self, df: DataFrame, col_name: str) -> DataFrame:
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
