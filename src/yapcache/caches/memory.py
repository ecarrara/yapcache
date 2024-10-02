from dataclasses import replace

import cachebox
from typing_extensions import Any, override

from yapcache.cache_item import NOT_FOUND, CacheItem, NotFound
from yapcache.caches import Cache


class InMemoryCache(Cache):
    def __init__(self, maxsize: int, capacity: int = 0, **kwargs):
        super().__init__(**kwargs)
        self._cache = cachebox.VTTLCache(maxsize=maxsize, capacity=capacity)

    @override
    async def get(self, key: str) -> CacheItem | NotFound:
        value, ttl = self._cache.get_with_expire(self._key(key), default=NOT_FOUND)
        if isinstance(value, NotFound):
            return value
        return replace(value, ttl=ttl)

    @override
    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None,
        best_before: float | None = None,
    ):
        return self._cache.insert(
            key=self._key(key),
            value=CacheItem(value=value, best_before=best_before, ttl=ttl),
            ttl=ttl,
        )
