import json
import time
from typing import Any, Optional
import redis.asyncio as redis
from app.config import settings

redis_client: Optional[redis.Redis] = None


class KVCache:
    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Optional[Any]:
        result = self._store.get(key)
        if result:
            value, expiry = result
            if expiry == 0 or time.time() < expiry:
                return value
            del self._store[key]
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        expiry = time.time() + ttl if ttl > 0 else 0
        self._store[key] = (value, expiry)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


kv_cache = KVCache()


async def get_redis() -> Optional[redis.Redis]:
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await redis_client.ping()
        except Exception:
            return None
    return redis_client


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    if r:
        try:
            val = await r.get(key)
            return json.loads(val) if val else None
        except Exception:
            pass
    return await kv_cache.get(key)


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    if r:
        try:
            await r.setex(key, ttl, json.dumps(value, default=str))
            return
        except Exception:
            pass
    await kv_cache.set(key, value, ttl)


async def cache_delete(key: str) -> None:
    r = await get_redis()
    if r:
        try:
            await r.delete(key)
        except Exception:
            pass
    await kv_cache.delete(key)
