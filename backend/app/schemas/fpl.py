from enum import Enum

from app.models.league_rules import FPLChip
from pydantic import BaseModel


class FPLPlayerPosition(str, Enum):
    GOALKEEPER = "GOALKEEPER"
    DEFENDER = "DEFENDER"
    MIDFIELDER = "MIDFIELDER"
    FORWARD = "FORWARD"

class FPLManagerResponse(BaseModel):
    entry_id: int
    team_name: str
    manager_name: str
    overall_points: int | None
    overall_rank: int | None

class FPLGameweekPickResponse(BaseModel):
    element_id: int

    player_name: str

    team_id: int
    team_name: str
    team_short_name: str

    player_position: FPLPlayerPosition

    squad_position: int
    is_starter: bool

    gameweek_points: int
    points_contribution: int

    multiplier: int
    is_captain: bool
    is_vice_captain: bool

class FPLGameweekResponse(BaseModel):
    entry_id: int
    gameweek: int

    gross_points: int
    transfer_deduction: int
    net_points: int

    transfers_made: int
    points_on_bench: int

    chip_used: FPLChip | None

    picks: list[FPLGameweekPickResponse]