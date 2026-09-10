from datetime import datetime
from enum import Enum

from app.db.base import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column


class GameweekResultStatus(str, Enum):
    LIVE = "LIVE"
    FINAL = "FINAL"


class GameweekIneligibilityReason(str, Enum):
    PROHIBITED_CHIP = "PROHIBITED_CHIP"


class GameweekResult(Base):
    __tablename__ = "gameweek_results"

    __table_args__ = (
        UniqueConstraint(
            "league_id",
            "league_member_id",
            "gameweek",
            name="uq_gameweek_result_member_gameweek",
        ),
        CheckConstraint(
            "gameweek BETWEEN 1 AND 38",
            name="ck_gameweek_result_gameweek",
        ),
        CheckConstraint(
            """
            (
                eligible = true
                AND ineligibility_reason IS NULL
            )
            OR
            (
                eligible = false
                AND ineligibility_reason IS NOT NULL
            )
            """,
            name="ck_gameweek_result_eligibility_reason",
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

    league_member_id: Mapped[int] = mapped_column(
        ForeignKey(
            "league_members.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    gameweek: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        index=True,
    )

    status: Mapped[GameweekResultStatus] = mapped_column(
        SQLEnum(
            GameweekResultStatus,
            name="gameweek_result_status",
        ),
        nullable=False,
    )

    gross_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    transfer_deduction: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    net_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    scoreboard_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    transfers_made: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
    )

    points_on_bench: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    chip_used: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    chip_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    eligible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    ineligibility_reason: Mapped[
        GameweekIneligibilityReason | None
    ] = mapped_column(
        SQLEnum(
            GameweekIneligibilityReason,
            name="gameweek_ineligibility_reason",
        ),
        nullable=True,
    )

    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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