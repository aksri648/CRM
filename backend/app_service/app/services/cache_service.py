import json
import time
from typing import Any, Optional


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


async def cache_get(key: str) -> Optional[Any]:
    return await kv_cache.get(key)


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    await kv_cache.set(key, value, ttl)


async def cache_delete(key: str) -> None:
    await kv_cache.delete(key)
