from enum import Enum

from app.db.base import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column


class FPLChip(str, Enum):
    WILDCARD = "WILDCARD"
    FREE_HIT = "FREE_HIT"
    BENCH_BOOST = "BENCH_BOOST"
    TRIPLE_CAPTAIN = "TRIPLE_CAPTAIN"


class LeagueRules(Base):
    __tablename__ = "league_rules"

    __table_args__ = (
        CheckConstraint(
            "start_gameweek BETWEEN 1 AND 38",
            name="ck_league_rules_start_gameweek",
        ),
    )

    league_id: Mapped[int] = mapped_column(
        ForeignKey(
            "leagues.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    start_gameweek: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    include_transfer_deductions: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    allowed_chips: Mapped[list[str]] = mapped_column(
        ARRAY(String(32)),
        nullable=False,
    )