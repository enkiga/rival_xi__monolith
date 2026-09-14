from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from redis.exceptions import RedisError

from app.core.cache import (
    delete_cached_keys,
    get_cached_json,
    set_cached_json,
)
from app.core.rate_limit import (
    RateLimitUnavailableError,
    enforce_rate_limit,
)


class CacheResilienceTests(IsolatedAsyncioTestCase):
    async def test_cache_read_failure_becomes_cache_miss(self):
        with patch(
            "app.core.cache.redis_client.get",
            new=AsyncMock(side_effect=RedisError),
        ):
            self.assertIsNone(await get_cached_json("key"))

    async def test_cache_write_and_delete_failures_do_not_break_request(self):
        with (
            patch(
                "app.core.cache.redis_client.set",
                new=AsyncMock(side_effect=RedisError),
            ),
            patch(
                "app.core.cache.redis_client.delete",
                new=AsyncMock(side_effect=RedisError),
            ),
        ):
            await set_cached_json("key", {"value": 1}, ttl=30)
            await delete_cached_keys("key")


class RateLimitResilienceTests(IsolatedAsyncioTestCase):
    async def test_rate_limit_failure_fails_closed(self):
        with patch(
            "app.core.rate_limit.redis_client.eval",
            new=AsyncMock(side_effect=RedisError),
        ):
            with self.assertRaises(RateLimitUnavailableError):
                await enforce_rate_limit(
                    scope="otp-request-email",
                    identifier="user@example.com",
                    limit=5,
                    window_seconds=900,
                )
