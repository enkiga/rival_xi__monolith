from datetime import datetime
from enum import Enum

from app.db.base import Base
from sqlalchemy import (
    DateTime,
    ForeignKey,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column


class LeagueMemberRole(str, Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class LeagueMemberStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LeagueMember(Base):
    __tablename__ = "league_members"

    __table_args__ = (
        UniqueConstraint(
            "league_id",
            "fpl_entry_id",
            name="uq_league_member_fpl_entry",
        ),
    )

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

    fpl_entry_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )

    role: Mapped[LeagueMemberRole] = mapped_column(
        SQLEnum(
            LeagueMemberRole,
            name="league_member_role",
        ),
        nullable=False,
        default=LeagueMemberRole.MEMBER,
        server_default=LeagueMemberRole.MEMBER.value,
    )

    status: Mapped[LeagueMemberStatus] = mapped_column(
        SQLEnum(
            LeagueMemberStatus,
            name="league_member_status",
        ),
        nullable=False,
        default=LeagueMemberStatus.PENDING,
        server_default=LeagueMemberStatus.PENDING.value,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    scoring_start_gameweek: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )