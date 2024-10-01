from yapcache import CacheItem


class BaseSerializer:
    def loads(self, value: bytes) -> CacheItem:
        raise NotImplementedError

    def dumps(self, value: CacheItem) -> bytes:
        raise NotImplementedError
