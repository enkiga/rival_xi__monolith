import logging
from datetime import datetime, timedelta, timezone

from app.db.session import AsyncSessionLocal
from app.integrations.fpl.client import (
    get_bootstrap_static,
    get_event_live,
)
from app.models.league import (
    League,
    LeagueStatus,
)
from app.models.league_member import (
    LeagueMember,
    LeagueMemberStatus,
)
from app.schemas.fpl import (
    FPLGameweekResponse,
)
from app.services.gameweek import (
    GameweekBeforeLeagueStartError,
    GameweekSyncDataError,
    sync_league_gameweek,
)
from app.services.notification import (
    notify_fpl_deadline,
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


def _get_next_event(
    bootstrap: dict,
) -> dict | None:
    for event in bootstrap.get(
        "events",
        [],
    ):
        if event.get("is_next"):
            return event

    return None


async def run_deadline_reminder_job() -> None:
    bootstrap = await get_bootstrap_static()
    event = _get_next_event(bootstrap)

    if event is None:
        return

    deadline_raw = event.get("deadline_time")

    if deadline_raw is None:
        return

    deadline = datetime.fromisoformat(
        deadline_raw.replace("Z", "+00:00")
    )
    now = datetime.now(timezone.utc)

    if not deadline - timedelta(hours=24) <= now < deadline:
        return

    gameweek = event["id"]

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(LeagueMember.user_id)
            .join(
                League,
                League.id == LeagueMember.league_id,
            )
            .where(
                League.status == LeagueStatus.ACTIVE,
                LeagueMember.status
                == LeagueMemberStatus.APPROVED,
                LeagueMember.user_id.is_not(None),
            )
            .distinct()
        )

        user_ids = list(result.scalars().all())

    async with AsyncSessionLocal() as db:
        async with db.begin():
            for user_id in user_ids:
                await notify_fpl_deadline(
                    db=db,
                    user_id=user_id,
                    gameweek=gameweek,
                    deadline_time=deadline_raw,
                )


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
