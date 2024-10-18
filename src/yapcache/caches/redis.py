from dataclasses import replace

from redis.asyncio.client import Redis
from typing_extensions import Any, override

from yapcache.cache_item import NOT_FOUND, CacheItem, NotFound
from yapcache.caches import Cache
from yapcache.serializers import BaseSerializer
from yapcache.serializers.pickle import PickleSerializer


class RedisCache(Cache):
    def __init__(
        self, client: Redis, serializer: BaseSerializer | None = None, **kwargs
    ):
        super().__init__(**kwargs)
        if serializer is None:
            serializer = PickleSerializer()
        self.serializer = serializer
        self._client = client

    @override
    async def get(self, key: str) -> CacheItem | NotFound:
        async with self._client.pipeline(transaction=True) as p:
            k = self._key(key)
            p.get(k)
            p.pttl(k)
            value, ttl = await p.execute()

            if ttl == -2:
                return NOT_FOUND

            if ttl == -1:
                ttl = None

            value = self.serializer.loads(value)
            return replace(value, ttl=ttl / 1000.0 if ttl else None)

    @override
    async def set(
        self,
        key: str,
        value: Any,
        ttl: float | None,
        best_before: float | None = None,
    ):
        await self._client.set(
            name=self._key(key),
            value=self.serializer.dumps(
                CacheItem(value=value, best_before=best_before)
            ),
            px=int(ttl * 1_000) if ttl is not None else None,
        )
