"""
Etsy Open API v3 client.
Handles auth, rate limiting, disk cache, and retry.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx

from app.config import settings


class EtsyRateLimiter:
    """Token bucket: ~10 req/sec, 10k/day. Conservative: 5 req/sec."""

    def __init__(self, rate: float = 5.0, burst: int = 10):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens < 1:
                wait = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= 1


class DiskCache:
    """JSON file cache keyed by request path+params. TTL in seconds."""

    def __init__(self, cache_dir: Path, default_ttl: int = 3600):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _key(self, path: str, params: dict[str, Any]) -> str:
        raw = f"{path}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, path: str, params: dict[str, Any]) -> Any | None:
        key = self._key(path, params)
        file = self.cache_dir / f"{key}.json"
        if not file.exists():
            return None
        try:
            data = json.loads(file.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - data.get("_cached_at", 0) > data.get("_ttl", self.default_ttl):
            file.unlink(missing_ok=True)
            return None
        return data.get("payload")

    def set(self, path: str, params: dict[str, Any], payload: Any, ttl: int | None = None) -> None:
        key = self._key(path, params)
        file = self.cache_dir / f"{key}.json"
        data = {
            "_cached_at": time.time(),
            "_ttl": ttl if ttl is not None else self.default_ttl,
            "payload": payload,
        }
        file.write_text(json.dumps(data))


class EtsyClient:
    """Async Etsy v3 client. All methods return raw JSON dicts."""

    BASE = "https://openapi.etsy.com/v3/application"

    def __init__(
        self,
        keystring: str,
        shared_secret: str,
        cache: DiskCache | None = None,
        rate_limiter: EtsyRateLimiter | None = None,
    ):
        self.keystring = keystring
        self.shared_secret = shared_secret
        self.cache = cache or DiskCache(Path("cache/etsy"))
        self.limiter = rate_limiter or EtsyRateLimiter()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE,
                headers={
                    "x-api-key": f"{self.keystring}:{self.shared_secret}",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        ttl: int | None = None,
    ) -> dict[str, Any]:
        params = params or {}

        # Cache check
        cached = self.cache.get(path, params)
        if cached is not None:
            return cached

        await self.limiter.acquire()
        client = await self._get_client()

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                resp = await client.request(method, path, params=params)
                if resp.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                data = resp.json()
                self.cache.set(path, params, data, ttl=ttl)
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (500, 502, 503):
                    await asyncio.sleep(2 ** attempt)
                    last_exc = e
                    continue
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                await asyncio.sleep(2 ** attempt)
                last_exc = e

        raise RuntimeError(f"Etsy request failed after retries: {last_exc}")

    # ---- Public API methods ----

    async def search_listings(
        self,
        keywords: str,
        limit: int = 100,
        offset: int = 0,
        sort_on: str = "score",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        """Search active listings. Returns ShopListings response."""
        return await self._request(
            "GET",
            "/listings/active",
            {
                "keywords": keywords,
                "limit": min(limit, 100),
                "offset": offset,
                "sort_on": sort_on,
                "sort_order": sort_order,
            },
            ttl=3600,
        )

    async def get_listing(self, listing_id: int) -> dict[str, Any]:
        """Single listing by ID."""
        return await self._request("GET", f"/listings/{listing_id}", ttl=1800)

    async def get_listing_reviews(
        self,
        listing_id: int,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Reviews for a listing (engagement signal)."""
        return await self._request(
            "GET",
            f"/listings/{listing_id}/reviews",
            {"limit": limit, "offset": offset},
            ttl=7200,
        )


# Module-level singleton (initialized in main.py lifespan)
_etsy_client: EtsyClient | None = None


def get_etsy_client() -> EtsyClient:
    if _etsy_client is None:
        raise RuntimeError("EtsyClient not initialized")
    return _etsy_client


def init_etsy_client() -> EtsyClient:
    global _etsy_client
    _etsy_client = EtsyClient(
        keystring=settings.ETSY_KEYSTRING,
        shared_secret=settings.ETSY_SHARED_SECRET,
        cache=DiskCache(Path("cache/etsy")),
    )
    return _etsy_client


async def close_etsy_client() -> None:
    global _etsy_client
    if _etsy_client:
        await _etsy_client.close()
        _etsy_client = None