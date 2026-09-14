from app.core.config import settings
from app.jobs.gameweek import (
    run_deadline_reminder_job,
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
        run_deadline_reminder_job,
        trigger="interval",
        minutes=30,
        id="fpl-deadline-reminder",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

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
