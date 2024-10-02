import asyncio
import uuid

from redis.asyncio import Redis
from typing_extensions import override


class DistLock:
    async def __aenter__(self):
        return await self.acquire()

    async def __aexit__(self, exc_type, exc, tb):
        await self.release()

    async def acquire(self):
        raise NotImplementedError

    async def release(self):
        raise NotImplementedError


class NullLock(DistLock):
    async def acquire(self):
        return

    async def release(self):
        return


class RedisDistLock(DistLock):
    RELEASE_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    _EVENTS: dict[str, asyncio.Event] = {}

    def __init__(
        self,
        client: Redis,
        resource_name: str,
        timeout: int = 30,
        delay_interval: float = 0.1,
        lease_time: int = 60,
    ):
        self.client = client
        self.resource_name = resource_name
        self.timeout = timeout
        self.delay_interval = delay_interval
        self.lease_time = lease_time
        self.lock_id = ""

    @override
    async def acquire(self):
        self.lock_id = str(uuid.uuid4())
        try:
            await asyncio.wait_for(self._acquire(), timeout=self.lease_time)
        except asyncio.TimeoutError:
            ...

    async def _acquire(self):
        while True:
            acquired = await self.client.set(
                self.resource_name, self.lock_id, nx=True, px=self.timeout * 1000
            )
            RedisDistLock._EVENTS[self.resource_name] = asyncio.Event()
            if acquired:
                return self

            # another coroutine in the same thread finished or `delay_interval` passed.
            try:
                await asyncio.wait_for(
                    RedisDistLock._EVENTS[self.resource_name].wait(),
                    timeout=self.delay_interval,
                )
            except asyncio.TimeoutError:
                ...

    @override
    async def release(self):
        released = await self.client.eval(
            self.RELEASE_LOCK_SCRIPT, 1, self.resource_name, self.lock_id
        )  # type: ignore
        if released:
            RedisDistLock._EVENTS.pop(self.resource_name).set()
