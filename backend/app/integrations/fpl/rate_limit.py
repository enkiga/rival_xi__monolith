import asyncio

from app.core.config import settings
from app.core.redis import redis_client

FPL_RATE_LIMIT_KEY = "rivalxi:v1:fpl:request-slot"


async def wait_for_fpl_request_slot() -> None:
    """
    Protect outbound requests to the FPL API.

    Ensures Rivalxi waits at least the configured
    interval between uncached FPL requests.
    """
    while True:
        acquired = await redis_client.set(
            FPL_RATE_LIMIT_KEY,
            "1",
            nx=True,
            px=settings.fpl_request_interval_ms,
        )

        if acquired:
            return

        remaining_ms = await redis_client.pttl(FPL_RATE_LIMIT_KEY)

        if remaining_ms <= 0:
            remaining_ms = 50

        await asyncio.sleep(remaining_ms / 1000)
