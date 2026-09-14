from datetime import datetime

from app.db.base import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column


class LeagueInvitation(Base):
    __tablename__ = "league_invitations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    league_id: Mapped[int] = mapped_column(
        ForeignKey(
            "leagues.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Only the SHA-256 hash is persisted.
    # The raw token exists only in the invite URL.
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )