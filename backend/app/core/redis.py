import time
from collections import OrderedDict, deque
from uuid import uuid4

from fastapi import Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.errors import ApiError

RATE_SCRIPT = """
local clock = redis.call('TIME')
local now = tonumber(clock[1]) * 1000 + math.floor(tonumber(clock[2]) / 1000)
local window = tonumber(ARGV[1])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window)
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[2]) then
    return 0
end
redis.call('ZADD', KEYS[1], now, ARGV[3])
redis.call('PEXPIRE', KEYS[1], window)
return 1
"""


class RateLimiter:
    def __init__(self, redis: Redis | None, policy: str, limit: int, window: int):
        self.redis = redis
        self.policy = policy
        self.limit = limit
        self.window = window
        self.recent: OrderedDict[str, deque[float]] = OrderedDict()

    def consume_local(self, identity: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window
        while self.recent and next(iter(self.recent.values()))[-1] <= cutoff:
            self.recent.popitem(last=False)

        hits = self.recent.setdefault(identity, deque())
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self.limit:
            return False
        hits.append(now)
        self.recent.move_to_end(identity)
        return True

    async def require(self, identity: str) -> None:
        accepted = None
        if self.redis is not None:
            try:
                accepted = await self.redis.eval(
                    RATE_SCRIPT, 1, f"course-select:limit:{self.policy}:{identity}",
                    self.window * 1000, self.limit, uuid4().hex,
                )
            except RedisError:
                pass
        if accepted is None:
            accepted = self.consume_local(identity)
        if not accepted:
            raise ApiError(
                429, "RATE_LIMITED", "请求过于频繁，请稍后重试",
                headers={"Retry-After": str(self.window)},
            )


async def limit_login(request: Request) -> None:
    identity = request.client.host if request.client else "unknown"
    await request.app.state.login_limiter.require(identity)
