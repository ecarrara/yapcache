# yapcache

[![PyPI - Version](https://img.shields.io/pypi/v/yapcache.svg)](https://pypi.org/project/yapcache)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/yapcache.svg)](https://pypi.org/project/yapcache)

Yet another Python cache library.

**Table of Contents**

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install yapcache
```

## Usage

In memory cache:

```python
import asyncio
from yapcache import memoize
from yapcache.caches.memory import InMemoryCache

cache = InMemoryCache(maxsize=1_000, key_prefix=f"example:")


@memoize(cache, ttl=60, cache_key=lambda n: f"slow-{n}")
async def slow_fn(n: int):
    await asyncio.sleep(n)


async def example():
    await slow_fn(3)
    await slow_fn(3)  # cached!


asyncio.run(example())
```

Redis cache:

```python
# ...
from redis.asyncio.client import Redis
from yapcache.caches.redis import RedisCache


redis_client = Redis()
cache = RedisCache(redis_client, key_prefix=f"example:")
```

Multi-layer cache:

```python
# ...
from yapcache.caches import MultiLayerCache

redis_client = Redis()

cache = MultiLayerCache(
    [InMemoryCache(maxsize=2_000), RedisCache(redis_client)],
    key_prefix=f"example:",
)
```

Use `lock` parameter to protect against thundering herd (only one coroutine/thread
will do the work and update the cache):

```python
# ...
from yapcache.distlock import RedisDistLock

@memoize(
    cache,
    ttl=60,
    cache_key=lambda n: f"slow-{n}",
    lock=lambda key: RedisDistLock(redis_client, key),
)
async def slow_fn(n: int):
    # ...
```

Use `best_before` to serve stale data (update the cache in background):

```python
@memoize(
    cache,
    ttl=60,
    cache_key=lambda n: f"slow-{n}",
    best_before=lambda n: time.time() + 30
)
async def slow_fn(n: int):
    # ...
```

## License

`yapcache` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
