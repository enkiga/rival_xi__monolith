from datetime import datetime
from enum import Enum

from app.db.base import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class NotificationType(str, Enum):
    MEMBERSHIP_APPROVED = "MEMBERSHIP_APPROVED"
    MEMBERSHIP_REJECTED = "MEMBERSHIP_REJECTED"

    MEMBERSHIP_PENDING = "MEMBERSHIP_PENDING"

    GAMEWEEK_WINNER = "GAMEWEEK_WINNER"
    FPL_DEADLINE = "FPL_DEADLINE"

    LEAGUE_RULES_CHANGED = "LEAGUE_RULES_CHANGED"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    type: Mapped[NotificationType] = mapped_column(
        SQLEnum(
            NotificationType,
            name="notification_type",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Used by scheduled/retryable events to
    # prevent duplicate notifications.
    dedupe_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Only used for notification types that
    # also require email delivery.
    email_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
