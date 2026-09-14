import json
import logging
from typing import TypeVar

from app.core.redis import redis_client
from pydantic import BaseModel
from pydantic import ValidationError
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

ModelT = TypeVar(
    "ModelT",
    bound=BaseModel,
)


async def get_cached_json(
    key: str,
) -> dict | list | None:
    try:
        value = await redis_client.get(key)

    except RedisError:
        logger.warning("Unable to read cache key %s", key)
        return None

    if value is None:
        return None

    try:
        return json.loads(value)

    except json.JSONDecodeError:
        logger.warning("Ignoring invalid JSON in cache key %s", key)
        return None


async def set_cached_json(
    key: str,
    value: dict | list,
    ttl: int,
) -> None:
    try:
        await redis_client.set(
            key,
            json.dumps(
                value,
                separators=(",", ":"),
            ),
            ex=ttl,
        )

    except RedisError:
        logger.warning("Unable to write cache key %s", key)


async def get_cached_model(
    key: str,
    model: type[ModelT],
) -> ModelT | None:
    try:
        value = await redis_client.get(key)

    except RedisError:
        logger.warning("Unable to read cache key %s", key)
        return None

    if value is None:
        return None

    try:
        return model.model_validate_json(value)

    except ValidationError:
        logger.warning("Ignoring invalid model in cache key %s", key)
        return None


async def set_cached_model(
    key: str,
    value: BaseModel,
    ttl: int,
) -> None:
    try:
        await redis_client.set(
            key,
            value.model_dump_json(),
            ex=ttl,
        )

    except RedisError:
        logger.warning("Unable to write cache key %s", key)


async def delete_cached_keys(
    *keys: str,
) -> None:
    if keys:
        try:
            await redis_client.delete(*keys)

        except RedisError:
            logger.warning("Unable to invalidate %s cache keys", len(keys))
