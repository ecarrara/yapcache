import asyncio

from typing_extensions import Any, Callable, Coroutine, ParamSpec, TypeVar, override

from yapcache.cache_item import NOT_FOUND, CacheItem, NotFound

P = ParamSpec("P")
R = TypeVar("R")


class Cache:
    def __init__(self, key_prefix: str = ""):
        self.key_prefix = key_prefix

    def _key(self, key):
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> CacheItem | NotFound:
        raise NotImplementedError

    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None,
        best_before: float | None = None,
    ):
        raise NotImplementedError

    async def close(self): ...

    def memoize(self, fn: Callable[P, Coroutine[Any, Any, R]], *args, **kwargs):
        from yapcache import memoize

        return memoize(self, *args, **kwargs)(fn)


class MultiLayerCache(Cache):
    def __init__(self, caches: list[Cache] = [], **kwargs):
        super().__init__(**kwargs)
        self.caches = caches

    @override
    async def close(self):
        await asyncio.gather(*(cache.close() for cache in self.caches))

    @override
    async def get(self, key: str) -> CacheItem | NotFound:
        key = self._key(key)
        found = NOT_FOUND

        index = 0
        for cache in self.caches:
            found = await cache.get(key)
            if found != NOT_FOUND:
                break
            index += 1

        if not isinstance(found, NotFound):
            await asyncio.gather(
                *(
                    cache.set(key, found.value, found.ttl)
                    for cache in self.caches[:index]
                )
            )
        return found

    @override
    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None,
        best_before: float | None = None,
    ):
        key = self._key(key)
        await asyncio.gather(
            *(cache.set(key, value, ttl, best_before) for cache in self.caches),
        )
