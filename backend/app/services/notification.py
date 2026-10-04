import logging
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.integrations.email.client import (
    EmailDeliveryError,
    send_notification_email,
)
from app.models.notification import (
    Notification,
    NotificationType,
)
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationResponse,
)
from sqlalchemy import (
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

logger = logging.getLogger(__name__)


EMAIL_NOTIFICATION_TYPES = {
    NotificationType.MEMBERSHIP_APPROVED,
    NotificationType.MEMBERSHIP_REJECTED,
}


class NotificationNotFoundError(Exception):
    pass


def notification_requires_email(
    notification_type: NotificationType,
) -> bool:
    return notification_type in EMAIL_NOTIFICATION_TYPES


def _notification_response(
    notification: Notification,
) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        body=notification.body,
        data=notification.data,
        read_at=notification.read_at,
        created_at=(notification.created_at),
    )


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    type: NotificationType,
    title: str,
    body: str,
    data: dict | None = None,
    dedupe_key: str | None = None,
) -> Notification:
    # Idempotency for events such as:
    #
    # gameweek winner
    # deadline reminder
    # approval/rejection retries
    if dedupe_key is not None:
        existing = await db.scalar(
            select(Notification).where(
                Notification.dedupe_key == dedupe_key,
            )
        )

        if existing is not None:
            return existing

    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        data=data or {},
        dedupe_key=dedupe_key,
    )

    db.add(notification)

    await db.flush()

    return notification


async def notify_membership_pending(
    db: AsyncSession,
    *,
    owner_user_id: int,
    league_id: int,
    league_slug: str,
    league_name: str,
    member_user_id: int,
    team_name: str,
) -> Notification:
    return await create_notification(
        db=db,
        user_id=owner_user_id,
        type=NotificationType.MEMBERSHIP_PENDING,
        title="New membership request",
        body=(
            f"{team_name} is waiting for approval "
            f"to join {league_name}."
        ),
        data={
            "league_id": league_id,
            "league_slug": league_slug,
            "member_user_id": member_user_id,
        },
    )


async def notify_membership_approved(
    db: AsyncSession,
    *,
    user_id: int,
    league_id: int,
    league_slug: str,
    league_name: str,
    member_count: int,
    max_member_count: int,
) -> Notification:
    return await create_notification(
        db=db,
        user_id=user_id,
        type=NotificationType.MEMBERSHIP_APPROVED,
        title="League membership approved",
        body=f"You've been approved to join {league_name}.",
        data={
            "league_id": league_id,
            "league_slug": league_slug,
            "league_name": league_name,
            "member_count": member_count,
            "max_member_count": max_member_count,
        },
    )


async def notify_membership_rejected(
    db: AsyncSession,
    *,
    user_id: int,
    league_id: int,
    league_slug: str,
    league_name: str,
    member_count: int,
    max_member_count: int,
) -> Notification:
    return await create_notification(
        db=db,
        user_id=user_id,
        type=NotificationType.MEMBERSHIP_REJECTED,
        title="League membership update",
        body=(
            f"Your request to join {league_name} "
            "was not approved."
        ),
        data={
            "league_id": league_id,
            "league_slug": league_slug,
            "league_name": league_name,
            "member_count": member_count,
            "max_member_count": max_member_count,
        },
    )


async def notify_league_rules_changed(
    db: AsyncSession,
    *,
    user_id: int,
    league_id: int,
    league_slug: str,
    league_name: str,
    changed_fields: list[str],
) -> Notification:
    return await create_notification(
        db=db,
        user_id=user_id,
        type=NotificationType.LEAGUE_RULES_CHANGED,
        title="League rules updated",
        body=f"The rules for {league_name} have been updated.",
        data={
            "league_id": league_id,
            "league_slug": league_slug,
            "changed_fields": changed_fields,
        },
    )


async def notify_gameweek_winner(
    db: AsyncSession,
    *,
    user_id: int,
    league_id: int,
    league_slug: str,
    league_name: str,
    gameweek: int,
    body: str,
) -> Notification:
    return await create_notification(
        db=db,
        user_id=user_id,
        type=NotificationType.GAMEWEEK_WINNER,
        title=f"Gameweek {gameweek} result",
        body=body,
        data={
            "league_id": league_id,
            "league_slug": league_slug,
            "league_name": league_name,
            "gameweek": gameweek,
        },
        dedupe_key=(
            f"gw-winner:{league_id}:{gameweek}:{user_id}"
        ),
    )


async def notify_fpl_deadline(
    db: AsyncSession,
    *,
    user_id: int,
    gameweek: int,
    deadline_time: str,
) -> Notification:
    return await create_notification(
        db=db,
        user_id=user_id,
        type=NotificationType.FPL_DEADLINE,
        title=f"Gameweek {gameweek} deadline",
        body=f"Gameweek {gameweek} deadline is approaching.",
        data={
            "gameweek": gameweek,
            "deadline_time": deadline_time,
        },
        dedupe_key=f"fpl-deadline:{gameweek}:{user_id}",
    )


async def deliver_notification_email(
    notification_id: int,
) -> bool:
    """
    Best-effort email delivery.

    Uses its own DB sessions so an external SMTP
    request is never held inside the domain
    transaction that created the notification.
    """

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                Notification,
                User.email,
            )
            .join(
                User,
                User.id == Notification.user_id,
            )
            .where(
                Notification.id == notification_id,
            )
        )

        row = result.first()

        if row is None:
            return False

        notification, email = row

        if not notification_requires_email(notification.type):
            return False

        if notification.email_sent_at is not None:
            return True

        subject = notification.title
        data = notification.data
        approved = notification.type == NotificationType.MEMBERSHIP_APPROVED

    # SMTP happens with no DB transaction open.
    try:
        await send_notification_email(
            email=email,
            subject=subject,
            approved=approved,
            league_name=data["league_name"],
            league_slug=data["league_slug"],
            member_count=data["member_count"],
            max_member_count=data["max_member_count"],
        )

    except EmailDeliveryError:
        logger.exception(
            "Unable to deliver notification email for notification %s",
            notification_id,
        )

        return False

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db, db.begin():
        await db.execute(
            update(Notification)
            .where(
                Notification.id == notification_id,
                Notification.email_sent_at.is_(None),
            )
            .values(email_sent_at=now)
        )

    return True


async def get_user_notifications(
    db: AsyncSession,
    *,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
) -> NotificationListResponse:
    query = (
        select(Notification)
        .where(
            Notification.user_id == user_id,
        )
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if unread_only:
        query = query.where(Notification.read_at.is_(None))

    result = await db.execute(query)

    notifications = result.scalars().all()

    unread_count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
    )

    return NotificationListResponse(
        items=[_notification_response(notification) for notification in notifications],
        unread_count=(unread_count or 0),
    )


async def get_unread_notification_count(
    db: AsyncSession,
    *,
    user_id: int,
) -> int:
    count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
    )

    return count or 0


async def mark_notification_read(
    db: AsyncSession,
    *,
    user_id: int,
    notification_id: int,
) -> NotificationResponse:
    now = datetime.now(timezone.utc)

    async with db.begin():
        notification = await db.scalar(
            select(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .with_for_update()
        )

        if notification is None:
            raise NotificationNotFoundError

        # Idempotent.
        if notification.read_at is None:
            notification.read_at = now

            await db.flush()

    return _notification_response(notification)


async def mark_all_notifications_read(
    db: AsyncSession,
    *,
    user_id: int,
) -> int:
    now = datetime.now(timezone.utc)

    async with db.begin():
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=now)
        )

    return result.rowcount
