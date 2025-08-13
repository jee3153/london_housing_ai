import pandas as pd
from typing import Dict, List, Optional
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


def extract_sold_year(df: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
    """Extract sold year data column out of given timestamp column

    Args:
        df (pd.DataFrame): original data frame
        timestamp_col (str): timestamp column name

    Returns:
        pd.DataFrame: dataframe which sold_year column is added
    """
    df["sold_year"] = df[timestamp_col].dt.year.astype("int64")
    return df


def extract_sold_month(df: pd.DataFrame, timestamp_col: str) -> pd.DataFrame:
    """Extract sold month data column out of given timestamp column

    Args:
        df (pd.DataFrame): original data frame
        timestamp_col (str): timestamp column name

    Returns:
        pd.DataFrame: dataframe which sold_month column is added
    """
    df["sold_month"] = df[timestamp_col].dt.month.astype("int64")
    return df


def extract_borough_price_trend(
    df: pd.DataFrame, extract_from: str, new_col: str
) -> pd.DataFrame:
    """extract price trend from median prices from each district.

    Args:
        df (pd.DataFrame): original data frame
        extract_from (str): column name the data is extracted from

    Returns:
        pd.DataFrame: data frame which "bourouch_price_trend" column is added.
    """
    district_medians = df.groupby(extract_from)["price"].median()

    df[new_col] = df[extract_from].map(district_medians)
    return df


def extract_yearly_district_price_trend(
    df: pd.DataFrame, district_col: str, years_col: str, new_col: str
) -> pd.DataFrame:
    """extract average prices per each (district, year_sold) pair.
    Before:
        ["district", "year_sold", "price", ...]
        ["camden", 2006, 234k, ...]
        ["camden", 2006, 190k, ...]
        ["camden", 2015, 334k, ...]
        ["camden", 2015, 300k, ...]

    After:
        [..., "district", "year_sold", "price", "district_yearly_medians"]
        [..., "camden", 2006, 234k, 212k]
        [..., "camden", 2006, 190k, 212k]
        [..., "camden", 2015, 334k, 284k]
        [..., "camden", 2015, 300k, 284k]

    Args:
        df (pd.DataFrame): original data frame
        district_col (str): column name of district
        years_col (str): column name of years
        new_col (str): column name of grouped median that will be added

    Returns:
        pd.DataFrame: _description_
    """
    district_yearly_medians = (
        # create a new grouped object prices grouped by district and years sold
        df.groupby(by=[district_col, years_col])["price"]
        .median()  # median of each group
        .reset_index()
        .rename(columns={"price": new_col})
    )
    # merge df + district_yearly_medians: df goes to the left.
    df = df.merge(district_yearly_medians, on=[district_col, years_col], how="left")
    return df


def extract_avg_price_last_6months(
    df: pd.DataFrame, new_col: str, date_col: str, district_col: str
) -> pd.DataFrame:
    """add column of average price for the last 6 months from the date of each row for each district.

    The extraction step:
    1. sort by `date` column

      district    date     price
    0  Camden  2020-01-01  700000
    3  Hackney 2020-01-15  500000
    1  Camden  2020-02-01  800000
    4  Hackney 2020-04-01  550000
    2  Camden  2020-06-01  750000

    2. group by `district` column
                district    date     price
    district
    Camden   0   Camden  2020-01-01  700000
             1   Camden  2020-02-01  800000
             2   Camden  2020-06-01  750000
    Hackney  3   Hackney 2020-01-15  500000
             4   Hackney 2020-04-01  550000

    3. remove group keys by group_keys=False
       district    date     price
    0   Camden  2020-01-01  700000
    1   Camden  2020-02-01  800000
    2   Camden  2020-06-01  750000
    3   Hackney 2020-01-15  500000
    4   Hackney 2020-04-01  550000

    4. set index by date column to each row in group
                    district    date     price
      date
    2020-01-01   0   Camden  2020-01-01  700000
    2020-02-01   1   Camden  2020-02-01  800000  << `Camden` group
    2020-06-01   2   Camden  2020-06-01  750000

    2020-01-15   3   Hackney 2020-01-15  500000  << `Hackney` group
    2020-04-01   4   Hackney 2020-04-01  550000

    5.  get median of 6month windows and select `price` column
        rolling window of 6 month from top to bottom.

       date     price    rolling 180D median
    2020-01-01  700k      700k << since only thing in the "6 month window" so far
    2020-02-01  800k      750k << median(700k, 800k) = (1st row, 2nd row)
    2020-07-01  750k      750k << median(750k, 800k) = (3rd row, 2nd row) in window. first row is not in 6 month window from current row

    2020-01-15  500k      500k
    2020-04-01  550k      525k

    Args:
        df (pd.DataFrame): original data frame
        new_col (str): column name for the last 6 months average price
        date_col (str): column name of date
        district_col (str): column name of district

    Returns:
        pd.DataFrame: data frame + column that calculated the last median
    """
    df_sorted_by_date = df.sort_values(date_col)
    # median price grouped by district (e.g. {"camden": 400k, "hackney": 350k, ...})
    district_medians = df.groupby("district")["price"].median()

    df_sorted_by_date[new_col] = (
        df_sorted_by_date.groupby(district_col, group_keys=False)
        .apply(
            # need to exclude district column since it's group key
            lambda group: _rolling_median(group.drop(columns=[district_col]), date_col)
        )
        .reset_index(drop=True)
    )

    df_sorted_by_date[new_col] = df_sorted_by_date[new_col].fillna(
        # map district column -> median price of each district using Series which can be represented using key: value map
        df_sorted_by_date["district"].map(district_medians)
    )
    return df_sorted_by_date


def _rolling_median(group: pd.DataFrame, date_col: str) -> pd.Series:
    # if there is no data of the last 180 days for the current row, it will return NaN
    return group.set_index(date_col)["price"].rolling("180D", closed="left").median()


def extract_interaction_features(
    df: pd.DataFrame, combi_col_name: str, col1: str, col2: str, sep: str = "_"
) -> pd.DataFrame:
    df[combi_col_name] = df[col1].astype(str) + sep + df[col2].astype(str)
    return df
