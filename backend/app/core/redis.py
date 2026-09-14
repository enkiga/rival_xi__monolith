from app.core.config import settings
from redis.asyncio import Redis

redis_client = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


async def initialize_redis() -> None:
    await redis_client.ping()


async def close_redis() -> None:
    await redis_client.aclose()