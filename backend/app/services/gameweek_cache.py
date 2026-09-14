from app.core.cache import (
    delete_cached_keys,
)
from app.core.config import settings
from app.models.gameweek_result import (
    GameweekResultStatus,
)


def standings_cache_key(
    slug: str,
    gameweek: int,
) -> str:
    return f"rivalxi:v1:league:{slug}:gw:{gameweek}:standings"


def member_gameweek_cache_key(
    slug: str,
    gameweek: int,
    member_id: int,
) -> str:
    return f"rivalxi:v1:league:{slug}:gw:{gameweek}:member:{member_id}"


def gameweek_response_ttl(
    status: GameweekResultStatus,
) -> int:
    if status == GameweekResultStatus.LIVE:
        return settings.live_gameweek_cache_ttl

    return settings.final_gameweek_cache_ttl


async def invalidate_gameweek_cache(
    slug: str,
    gameweek: int,
    member_ids: list[int],
) -> None:
    keys = [
        standings_cache_key(
            slug,
            gameweek,
        )
    ]

    keys.extend(
        member_gameweek_cache_key(
            slug,
            gameweek,
            member_id,
        )
        for member_id in member_ids
    )

    await delete_cached_keys(*keys)
