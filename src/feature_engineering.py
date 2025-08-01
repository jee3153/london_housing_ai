import pandas as pd
from typing import Dict, List, Any, Optional
import numpy as np
from numpy import ndarray
import requests
import time
import asyncio, aiohttp, async_timeout, time

POSTCODE_URL = "https://api.postcodes.io/postcodes"
MAX_PER_REQ = 100
MAX_CONCURRENCY = 10
RATE_SLEEP = 0.12
MAX_RETRIES = 3
BACKOFF_FACTOR = 2

# create concurrent async coroutine
_sem = asyncio.Semaphore(MAX_CONCURRENCY)


async def get_district_from_postcode(
    df: pd.DataFrame,
    postcode_col: str,
    district_col: str,
    batch_size: int = MAX_PER_REQ,
) -> pd.DataFrame:
    unique_postcodes = df[postcode_col].dropna().unique().tolist()
    failed, mapping = [], {}

    async with aiohttp.ClientSession(
        headers={"User-Agent": "LondonHousing/0.1"}
    ) as session:
        # returns List[Dict[poscode, district]] and each item is coroutine
        postcode_to_district_map, failed = await _fetch_districts_with_retries(
            session, unique_postcodes, batch_size
        )

    # keep only rows with postcode is not in failed list
    df = df.loc[~df[postcode_col].isin(failed), :].copy()
    df.loc[:, district_col] = df[postcode_col].map(postcode_to_district_map)
    print(f"getting district from postcodes is complete. failed queries: {failed}")
    return df


def _chunk(chunkable: List[str], n: int) -> List[List[str]]:
    return [chunkable[i : i + n] for i in range(0, len(chunkable), n)]


async def _bulk_lookup(
    session: aiohttp.ClientSession, postcodes: List[str]
) -> Optional[List[dict]]:
    """
    A *single* hit to the bulk‑lookup endpoint.
    Returns the parsed JSON on success, or None on transport/HTTP errors.
    """
    body = {"postcodes": postcodes}

    async with _sem:
        try:
            async with async_timeout.timeout(30):
                res = await session.post(POSTCODE_URL, json=body)

            if res.status == 429:
                return

            res.raise_for_status()
            return (await res.json())["result"]

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return


async def _fetch_districts_with_retries(
    session: aiohttp.ClientSession,
    postcodes: List[str],
    batch_size: int = MAX_PER_REQ,
    concurrency: int = MAX_CONCURRENCY,
    max_retries: int = MAX_RETRIES,
    backoff_factor: int = BACKOFF_FACTOR,
    rate_sleep: float = RATE_SLEEP,
) -> tuple[Dict[str, str], List[str]]:
    """
    Resolves every postcode independently:

    • Makes batched calls for efficiency.
    • On each pass, only the *still‑unresolved* codes are retried.
    • Stops after `max_retries` attempts for each individual code.

    Returns (resolved_mapping, failed_list).
    """
    todo = {pc.upper() for pc in postcodes}
    done: Dict[str, str] = {}

    for attempt in range(max_retries):
        if not todo:
            break

        resolved = await _one_round(session, list(todo), batch_size)
        done.update(resolved)
        todo.difference_update(done.keys())
        print(f"[attempt {attempt}] todo={len(todo)} resolved={len(done)}")

        # back-off only if there is still work to do
        if todo:
            await asyncio.sleep(backoff_factor * (2**attempt))

    return done, sorted(todo)


async def _one_round(
    session: aiohttp.ClientSession, todo: List[str], batch_size: int
) -> Dict[str, str]:
    chunks = _chunk(todo, batch_size)
    print(f"wave: {len(chunks)} chunks of <=100")

    tasks = []
    async with asyncio.TaskGroup() as task_group:
        for c in chunks:
            tasks.append(task_group.create_task(_bulk_lookup(session, c)))

    # all tasks finished here
    out: Dict[str, str] = {}
    for t in tasks:
        data = t.result()  # None if that whole chunk failed
        if not data:
            continue
        for row in data:
            pc = row["query"]

            result = row.get("result")
            if result is None:
                continue

            district = result.get("admin_district")
            if district:
                out[pc] = district
    return out


def merge_categories(df: pd.DataFrame, merge_map: Dict[str, List[str]]) -> pd.DataFrame:
    updated_df = df.copy()
    for merge_to, merge_froms in merge_map.items():
        updated_df = df.replace(merge_froms, merge_to)
    return updated_df


def drop_niche_categories(df: pd.DataFrame, col_name: str, count: int) -> pd.DataFrame:
    """
    Filters values of column that are >= configured count
    """
    return df[df[col_name].map(df[col_name].value_counts()) >= count]


def filter_by_keywords(
    df: pd.DataFrame, keywords: List[str], col_name: str
) -> pd.DataFrame:
    for keyword in keywords:
        mask = df[col_name].str.contains(keyword, case=False, na=False)
    return df[mask]
