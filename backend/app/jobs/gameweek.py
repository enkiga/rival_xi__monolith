import logging

from app.db.session import AsyncSessionLocal
from app.integrations.fpl.client import (
    get_bootstrap_static,
    get_event_live,
)
from app.models.league import (
    League,
    LeagueStatus,
)
from app.schemas.fpl import (
    FPLGameweekResponse,
)
from app.services.gameweek import (
    GameweekBeforeLeagueStartError,
    GameweekSyncDataError,
    sync_league_gameweek,
)
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _get_current_event(
    bootstrap: dict,
) -> dict | None:
    for event in bootstrap.get(
        "events",
        [],
    ):
        if event.get("is_current"):
            return event

    return None


async def run_gameweek_sync_job() -> None:
    try:
        bootstrap = await get_bootstrap_static()

        event = _get_current_event(bootstrap)

        if event is None:
            return

        gameweek = event["id"]

        # FPL's current event should normally
        # already have passed its deadline.
        # We still guard against bad assumptions.
        from app.services.gameweek import (
            validate_gameweek_started,
        )

        validate_gameweek_started(event)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(League.slug).where(League.status == LeagueStatus.ACTIVE)
            )

            league_slugs = list(result.scalars().all())

        if not league_slugs:
            return

        # Shared across every league in this run.
        live_data = await get_event_live(
            gameweek=gameweek,
        )

        fpl_gameweek_cache: dict[
            int,
            FPLGameweekResponse,
        ] = {}

        # Sequential intentionally.
        # Avoid a burst of simultaneous FPL requests.
        for slug in league_slugs:
            try:
                async with AsyncSessionLocal() as db:
                    await sync_league_gameweek(
                        db=db,
                        slug=slug,
                        gameweek=gameweek,
                        bootstrap=bootstrap,
                        live_data=live_data,
                        fpl_gameweek_cache=(fpl_gameweek_cache),
                    )

            except GameweekBeforeLeagueStartError:
                continue

            except GameweekSyncDataError:
                logger.exception(
                    "Unable to sync league %s for gameweek %s",
                    slug,
                    gameweek,
                )

            except Exception:
                logger.exception(
                    "Unexpected error syncing league %s for gameweek %s",
                    slug,
                    gameweek,
                )

    except Exception:
        logger.exception("Gameweek synchronization job failed")
