import sys
import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import Generic

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self):
            return str(self.value)


from typing_extensions import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Optional,
    ParamSpec,
    TypeVar,
    Concatenate,
)

from yapcache.cache_item import CacheItem
from yapcache.caches import Cache
from yapcache.distlock import DistLock, NullLock

P = ParamSpec("P")
R = TypeVar("R")


class CacheStatus(StrEnum):
    HIT = "hit"
    MISS = "miss"
    STALE = "stale"


@dataclass
class MemoizeResult(Generic[R]):
    cache_status: CacheStatus
    result: R


def memoize(
    cache: Cache,
    cache_key: Callable[P, str],
    ttl: float | Callable[Concatenate[R, P], float],
    best_before: Callable[Concatenate[R, P], Optional[float]] = lambda _,
    *a,
    **kw: None,
    lock: Callable[[str], DistLock] = lambda *a, **kw: NullLock(),
    process_result: Callable[[MemoizeResult[R]], R] = lambda r, *a, **kw: r.result,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    update_tasks: dict[str, asyncio.Task] = {}

    def decorator(fn: Callable[P, Awaitable[R]]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            key = cache_key(*args, **kwargs)

            async def _call_with_lock():
                async with lock(key + ":lock"):
                    found = await cache.get(
                        key
                    )  # did someone populate the cache while I was waiting for the lock?
                    if isinstance(found, CacheItem) and not found.is_stale:
                        return MemoizeResult(
                            result=found.value, cache_status=CacheStatus.HIT
                        )

                    result = await fn(*args, **kwargs)

                    await cache.set(
                        key,
                        value=result,
                        ttl=ttl(result, *args, **kwargs) if callable(ttl) else ttl,
                        best_before=best_before(result, *args, **kwargs),
                    )

                    return MemoizeResult(result=result, cache_status=CacheStatus.MISS)

            found = await cache.get(key)
            if isinstance(found, CacheItem):
                status = CacheStatus.HIT
                if found.is_stale and key not in update_tasks:
                    task = asyncio.create_task(_call_with_lock())
                    update_tasks[key] = task  # TODO: acho que tem problema
                    task.add_done_callback(lambda _: update_tasks.pop(key))
                    status = CacheStatus.STALE
                return process_result(
                    MemoizeResult(result=found.value, cache_status=status),
                    *args,
                    **kwargs,
                )

            result = await _call_with_lock()

            return process_result(result, *args, **kwargs)

        return wrapper

    return decorator
