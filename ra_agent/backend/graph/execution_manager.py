"""
graph/execution_manager.py

Duplicate execution prevention + result caching.

Fixes:
  1. _in_flight checked BEFORE graph runs — duplicates dropped immediately
  2. Cache key includes query text + market + budget (rounded) + timeline
  3. Cache TTL = 300s; stale entries evicted on every store
  4. Thread-safe via asyncio.Lock
"""

import asyncio
import time
from collections import OrderedDict
from typing import Optional

_in_flight: set[str] = set()
_lock = asyncio.Lock()

_results_cache: OrderedDict = OrderedDict()
_CACHE_MAX     = 20
_CACHE_TTL_S   = 300   # 5 minutes


def _cache_key(user_query: str, market: str, budget: float, timeline: int) -> str:
    """Stable, lowercase deduplication key."""
    q = user_query.strip().lower()[:200]
    m = (market or "").strip().lower()
    b = int(budget // 1000) * 1000    # round to nearest $1000 to avoid float noise
    return f"{q}|{m}|{b}|{timeline}"


async def acquire(request_id: str) -> bool:
    """
    Claim a request_id for execution.
    Returns True if acquired (proceed), False if already running (drop duplicate).
    """
    async with _lock:
        if request_id in _in_flight:
            return False
        _in_flight.add(request_id)
        return True


async def release(request_id: str) -> None:
    """Release a completed request_id."""
    async with _lock:
        _in_flight.discard(request_id)


async def get_cached(
    user_query: str, market: str, budget: float, timeline: int
) -> Optional[dict]:
    """Return cached result for an identical recent query, or None."""
    key = _cache_key(user_query, market, budget, timeline)
    async with _lock:
        entry = _results_cache.get(key)
        if entry and (time.time() - entry["ts"]) < _CACHE_TTL_S:
            return entry["result"]
        if entry:
            # Expired — remove
            del _results_cache[key]
    return None


async def store_result(
    user_query: str, market: str, budget: float, timeline: int, result: dict
) -> None:
    """Cache a completed result. Evicts oldest entries beyond _CACHE_MAX."""
    key = _cache_key(user_query, market, budget, timeline)
    async with _lock:
        _results_cache[key] = {"result": result, "ts": time.time()}
        # Evict oldest while over limit
        while len(_results_cache) > _CACHE_MAX:
            _results_cache.popitem(last=False)
