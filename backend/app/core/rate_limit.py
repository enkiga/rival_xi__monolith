import hashlib

from app.core.redis import redis_client
from redis.exceptions import RedisError


class RateLimitExceededError(Exception):
    def __init__(
        self,
        retry_after: int,
    ):
        self.retry_after = retry_after

        super().__init__("Rate limit exceeded")


class RateLimitUnavailableError(Exception):
    pass


RATE_LIMIT_SCRIPT = """
local current = redis.call(
    "INCR",
    KEYS[1]
)

if current == 1 then
    redis.call(
        "EXPIRE",
        KEYS[1],
        ARGV[1]
    )
end

local ttl = redis.call(
    "TTL",
    KEYS[1]
)

return {
    current,
    ttl
}
"""


def _identifier_hash(
    value: str,
) -> str:
    """
    Avoid storing raw identifiers such as email
    addresses or IP addresses in Redis keys.
    """
    return hashlib.sha256(value.encode()).hexdigest()


async def enforce_rate_limit(
    *,
    scope: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> None:
    """
    Generic fixed-window rate limiter.

    Intended for endpoints such as:
    - OTP requests
    - OTP verification
    - other user-facing abuse-sensitive operations

    FPL outbound pacing continues to use
    wait_for_fpl_request_slot().
    """
    identifier_hash = _identifier_hash(identifier)

    key = f"rivalxi:v1:rate-limit:{scope}:{identifier_hash}"

    try:
        result = await redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            window_seconds,
        )

    except RedisError as exc:
        raise RateLimitUnavailableError from exc

    count = int(result[0])

    ttl = int(result[1])

    if count > limit:
        raise RateLimitExceededError(
            retry_after=max(
                ttl,
                1,
            )
        )
