from typing import Any
from yapcache.cache_item import NOT_FOUND, CacheItem, NotFound
from yapcache.caches import Cache


class NullCache(Cache):

    async def get(self, key: str) -> CacheItem | NotFound:
        return NOT_FOUND

    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None,
        best_before: float | None = None,
    ):
        ... # no-op

    async def delete(self, key: str) -> bool:
        ... # no-op
