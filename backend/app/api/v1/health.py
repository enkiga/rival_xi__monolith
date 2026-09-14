from app.core.redis import redis_client
from app.db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "rivalxi-api",
    }

@router.get("/health/db")
async def database_health_check(
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    result = await db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": result.scalar_one(),
    }


@router.get("/health/redis")
async def redis_health_check():
    try:
        await redis_client.ping()

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is unavailable",
        )

    return {
        "status": "ok",
        "redis": "ok",
    }
