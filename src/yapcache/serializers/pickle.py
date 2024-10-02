import pickle

from typing_extensions import override

from yapcache import CacheItem
from yapcache.serializers import BaseSerializer


class PickleSerializer(BaseSerializer):
    @override
    def loads(self, value: bytes) -> CacheItem:
        return pickle.loads(value)

    @override
    def dumps(self, value: CacheItem) -> bytes:
        return pickle.dumps(value)
