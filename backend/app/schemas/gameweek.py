from app.models.gameweek_result import (
    GameweekIneligibilityReason,
    GameweekResultStatus,
)
from app.models.league_rules import FPLChip
from app.schemas.fpl import FPLPlayerPosition
from pydantic import BaseModel


class RivalxiGameweekScore(BaseModel):
    entry_id: int
    gameweek: int

    gross_points: int
    transfer_deduction: int
    net_points: int
    scoreboard_points: int

    transfers_made: int
    points_on_bench: int

    chip_used: FPLChip | None
    chip_allowed: bool

    eligible: bool
    ineligibility_reason: GameweekIneligibilityReason | None


class GameweekSyncMemberResponse(BaseModel):
    league_member_id: int
    entry_id: int

    scoreboard_points: int

    chip_used: FPLChip | None

    eligible: bool

    ineligibility_reason: GameweekIneligibilityReason | None


class LeagueGameweekSyncResponse(BaseModel):
    league_slug: str
    gameweek: int
    status: GameweekResultStatus

    synced_members: int

    results: list[GameweekSyncMemberResponse]

class GameweekStandingResponse(BaseModel):
    rank: int | None

    league_member_id: int
    fpl_entry_id: int

    gross_points: int
    transfer_deduction: int
    net_points: int
    scoreboard_points: int

    transfers_made: int
    points_on_bench: int

    chip_used: FPLChip | None
    chip_allowed: bool

    eligible: bool

    ineligibility_reason: (
        GameweekIneligibilityReason | None
    )

    ineligibility_label: str | None


class LeagueGameweekResponse(BaseModel):
    league_slug: str
    gameweek: int
    status: GameweekResultStatus

    standings: list[
        GameweekStandingResponse
    ]


class GameweekPickResponse(BaseModel):
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


class MemberGameweekResponse(BaseModel):
    league_member_id: int
    fpl_entry_id: int

    gameweek: int
    status: GameweekResultStatus

    rank: int | None

    gross_points: int
    transfer_deduction: int
    net_points: int
    scoreboard_points: int

    transfers_made: int
    points_on_bench: int

    chip_used: FPLChip | None
    chip_allowed: bool

    eligible: bool

    ineligibility_reason: (
        GameweekIneligibilityReason | None
    )

    ineligibility_label: str | None

    picks: list[GameweekPickResponse]