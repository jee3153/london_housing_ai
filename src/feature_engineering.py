import pandas as pd
from typing import Dict, List, Any
import numpy as np
from numpy import ndarray
import requests
import time
import asyncio, aiohttp, async_timeout, time

POSTCODE_URL = "https://api.postcodes.io/postcodes"
MAX_PER_REQ = 100
MAX_CONCURRENCY = 10
RATE_SLEEP = 0.12

_sem = asyncio.Semaphore(MAX_CONCURRENCY)


async def get_district_from_postcode(
    df: pd.DataFrame,
    postcode_col: str,
    district_col: str,
    batch_size: int = MAX_PER_REQ
) -> pd.DataFrame:
    unique_postcodes = df[postcode_col].unique()
    failed, mapping = [], {}

    async with aiohttp.ClientSession(
        headers={"User-Agent": "LondonHousing/0.1"}
    ) as session:
        # returns List[Dict[poscode, district]] and each item is coroutine
        tasks = [
            _fetch_district_async(
                session,
                unique_postcodes[i:i+batch_size].tolist(),
                failed
            )
            for i in range(0, len(unique_postcodes), batch_size)
        ]

        # launch in waves of 10 coroutines
        for i in range(0, len(tasks), MAX_CONCURRENCY):
            wave = tasks[i: i + MAX_CONCURRENCY]
            for res in await asyncio.gather(*wave):
                mapping.update(res)
            await asyncio.sleep(RATE_SLEEP)

    df = df.loc[~df[postcode_col].isin(failed), :]
    df.loc[:, district_col] = df[postcode_col].map(mapping)
    print(f"getting district from postcodes is complete. failed queries: {failed}")        
    return df        


"""
Fetch admin_district for up to 100 postcodes per single API call.
"""
async def _fetch_district_async(
        session: aiohttp.ClientSession,
        postcodes: List[str],
        failed: List[str],
) -> Dict[str, str]:
    body = {"postcodes": postcodes}
    async with _sem:
        async with async_timeout.timeout(15):
            res = await session.post(POSTCODE_URL, json=body)
            if res.status == 429:
                await asyncio.sleep(2) # sleep for 2 sec
                res = await session.post(POSTCODE_URL, json=body)
            res.raise_for_status()
            data = (await res.json())["result"]

    out = {}
    for row in data:
        postcode = row["query"]
        district_per_postcode = row.get("result")
        if not district_per_postcode or "admin_district" not in district_per_postcode:
            failed.append(postcode)
            continue
        out[postcode] = district_per_postcode["admin_district"]
    return out                



    

def merge_categories(df: pd.DataFrame, merge_map: Dict[str, List[str]]) -> pd.DataFrame:
    updated_df = df.copy()
    for merge_to, merge_froms in merge_map.items():
        updated_df = df.replace(merge_froms, merge_to)
    return updated_df 


"""
    Filters values of column that are >= configured count
"""
def drop_niche_categories(df: pd.DataFrame, col_name: str, count: int) -> pd.DataFrame:
    return df[df[col_name].map(df[col_name].value_counts()) >= count]


def filter_by_keywords(df: pd.DataFrame, keywords: List[str], col_name: str) -> pd.DataFrame:
    for keyword in keywords:
        mask = df[col_name].str.contains(keyword, case=False, na=False)
    return df[mask]  


"""
Fill in locations based on postcode, to get consistent categories for locations
"""
def map_postcodes_to_locations(df: pd.DataFrame, postcode_col: str, new_column_name: str) ->pd. DataFrame:
    unique_postcodes = df[postcode_col].unique()
    batch_size = 100
    failed_queries = []
    postcode_location_map = {}

    for i in range(0, len(unique_postcodes), batch_size):
        batch = unique_postcodes[i:i + batch_size]
        postcode_location_map.update(_fetch_district(batch, failed_queries))

    _handle_failed_postcodes(df, failed_queries, postcode_col)
    df.loc[:, new_column_name] = df.loc[:, postcode_col].map(postcode_location_map)
    return df


def _handle_failed_postcodes(df: pd.DataFrame, failed_queries: List[str], postcode_col: str) -> pd.DataFrame:
        return df.loc[~df[postcode_col].isin(failed_queries), :]


def _fetch_district(postcodes: ndarray, failed_queries: List[str]) -> Dict[Any, Any]:
    url = "https://api.postcodes.io/postcodes"
    headers = {"Content-Type": "application/json"}
    payload = {"postcodes": list(postcodes)}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # back-off & retry once
        if response.status_code == 429:
            time.sleep(2)
            response = requests.post(url, json=payload, headers=headers, timeout=10)

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
    