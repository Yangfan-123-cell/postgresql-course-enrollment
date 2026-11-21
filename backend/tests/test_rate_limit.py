import asyncio

import pytest
from fakeredis.aioredis import FakeRedis

from app.core.errors import ApiError
from app.core.redis import RateLimiter


def test_redis_limits_are_shared_and_scoped_to_the_identity():
    async def check_limit():
        async with FakeRedis() as redis:
            first = RateLimiter(redis, "login", limit=5, window=60)
            second = RateLimiter(redis, "login", limit=5, window=60)
            for _ in range(3):
                await first.require("address-one")
            for _ in range(2):
                await second.require("address-one")
            with pytest.raises(ApiError) as error:
                await second.require("address-one")
            assert error.value.status == 429
            assert error.value.code == "RATE_LIMITED"
            assert 0 < await redis.pttl("course-select:limit:login:address-one") <= 60_000
            await second.require("address-two")

    asyncio.run(check_limit())
