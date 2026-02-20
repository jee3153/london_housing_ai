from __future__ import annotations

import asyncio
from typing import Optional
from urllib.parse import quote

import aiohttp
import async_timeout

from london_housing_ai.utils.logger import get_logger

POSTCODE_LOOKUP_URL = "https://api.postcodes.io/postcodes/{postcode}"
_cache: dict[str, Optional[str]] = {}
_lock = asyncio.Lock()
_session: Optional[aiohttp.ClientSession] = None
logger = get_logger()


def _normalize_postcode(postcode: str) -> str:
    return postcode.replace(" ", "").upper()


def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(headers={"User-Agent": "LondonHousing/0.1"})
    return _session


async def resolve_district(postcode: str, timeout_seconds: int = 10) -> Optional[str]:
    """
    Resolve a single postcode to its admin district using postcodes.io.
    Returns None for unknown/invalid postcodes or transient lookup errors.
    """
    if not postcode or not postcode.strip():
        return None

    normalized = _normalize_postcode(postcode)
    async with _lock:
        if normalized in _cache:
            return _cache[normalized]

    url = POSTCODE_LOOKUP_URL.format(postcode=quote(normalized))
    district: Optional[str] = None

    # Make HTTP call
    try:
        async with get_session() as session:
            async with async_timeout.timeout(timeout_seconds):
                async with session.get(url) as response:
                    if response.status == 404:
                        district = None
                    else:
                        response.raise_for_status()
                        payload = await response.json()
                        result = payload.get("result") or {}
                        district = result.get("admin_district")
    except (aiohttp.ClientError, asyncio.TimeoutError):
        logger.warning("Postcode lookup failed for postcode=%s", normalized)
        return None

    async with _lock:
        _cache[normalized] = district
    return district
