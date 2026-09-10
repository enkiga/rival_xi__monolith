from app.core.config import settings
from app.jobs.gameweek import (
    run_gameweek_sync_job,
)
from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,
)

scheduler = AsyncIOScheduler(
    timezone="UTC",
)


def start_scheduler() -> None:
    scheduler.add_job(
        run_gameweek_sync_job,
        trigger="interval",
        minutes=(
            settings
            .gameweek_sync_interval_minutes
        ),
        id="live-gameweek-sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )

    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(
            wait=False,
        )