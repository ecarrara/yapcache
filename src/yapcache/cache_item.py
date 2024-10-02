import time
from dataclasses import dataclass

from typing_extensions import Any


@dataclass(frozen=True, slots=True, eq=True)
class CacheItem:
    """A value retrievied from cache."""

    value: Any
    """The cached value."""

    ttl: float | None = None
    """Time-to-live in seconds."""

    best_before: float | None = None
    """Best before this timestamp."""

    @property
    def is_stale(self):
        if self.best_before is None:
            return False
        return time.time() > self.best_before


class NotFound: ...


NOT_FOUND = NotFound()
