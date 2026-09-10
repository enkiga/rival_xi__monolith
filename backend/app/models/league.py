from datetime import datetime
from enum import Enum

from app.db.base import Base
from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column


class LeagueStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[LeagueStatus] = mapped_column(
        SQLEnum(
            LeagueStatus,
            name="league_status",
        ),
        nullable=False,
        default=LeagueStatus.DRAFT,
        server_default=LeagueStatus.DRAFT.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )