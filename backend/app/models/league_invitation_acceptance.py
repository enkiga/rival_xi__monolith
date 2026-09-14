from datetime import datetime

from app.db.base import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column


class LeagueInvitationAcceptance(Base):
    __tablename__ = "league_invitation_acceptances"

    __table_args__ = (
        UniqueConstraint(
            "invitation_id",
            "user_id",
            name=(
                "uq_league_invitation_acceptance_user"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    invitation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "league_invitations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    accepted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )