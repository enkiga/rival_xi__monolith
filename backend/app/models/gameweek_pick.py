from app.db.base import Base
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column


class GameweekPick(Base):
    __tablename__ = "gameweek_picks"

    __table_args__ = (
        UniqueConstraint(
            "gameweek_result_id",
            "element_id",
            name="uq_gameweek_pick_element",
        ),
        UniqueConstraint(
            "gameweek_result_id",
            "squad_position",
            name="uq_gameweek_pick_squad_position",
        ),
        CheckConstraint(
            "squad_position BETWEEN 1 AND 15",
            name="ck_gameweek_pick_squad_position",
        ),
        CheckConstraint(
            "multiplier BETWEEN 0 AND 3",
            name="ck_gameweek_pick_multiplier",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    gameweek_result_id: Mapped[int] = mapped_column(
        ForeignKey(
            "gameweek_results.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    element_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    player_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    team_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    team_short_name: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    player_position: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    squad_position: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    is_starter: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    gameweek_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    points_contribution: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    multiplier: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )

    is_captain: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_vice_captain: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )