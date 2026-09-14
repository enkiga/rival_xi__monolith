from datetime import datetime

from app.models.league import LeagueStatus
from app.models.league_member import (
    LeagueMemberRole,
    LeagueMemberStatus,
)
from app.models.league_rules import FPLChip
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LeagueRulesCreate(BaseModel):
    start_gameweek: int = Field(
        ge=1,
        le=38,
    )

    include_transfer_deductions: bool

    allowed_chips: list[FPLChip] = Field(
        max_length=4,
    )

    @field_validator("allowed_chips")
    @classmethod
    def unique_chips(
        cls,
        chips: list[FPLChip],
    ) -> list[FPLChip]:
        if len(chips) != len(set(chips)):
            raise ValueError("Allowed chips must be unique")

        return chips

class LeagueCreate(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=100,
    )

    rules: LeagueRulesCreate

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

class LeagueRulesResponse(BaseModel):
    start_gameweek: int
    include_transfer_deductions: bool
    allowed_chips: list[FPLChip]


class LeagueMemberResponse(BaseModel):
    id: int
    fpl_entry_id: int
    role: LeagueMemberRole
    status: LeagueMemberStatus
    joined_at: datetime
    approved_at: datetime | None
    scoring_start_gameweek: int | None


class LeagueResponse(BaseModel):
    id: int
    name: str
    slug: str
    status: LeagueStatus
    created_at: datetime
    started_at: datetime | None

    rules: LeagueRulesResponse
    owner: LeagueMemberResponse

class LeagueDetailResponse(BaseModel):
    id: int
    name: str
    slug: str
    status: LeagueStatus
    created_at: datetime
    started_at: datetime | None
    rules: LeagueRulesResponse
    members: list[LeagueMemberResponse]

class LeagueStatusResponse(BaseModel):
    id: int
    name: str
    slug: str
    status: LeagueStatus
    started_at: datetime | None

class LeagueRulesUpdate(BaseModel):
    start_gameweek: int | None = Field(
        default=None,
        ge=1,
        le=38,
    )

    include_transfer_deductions: bool | None = None

    allowed_chips: list[FPLChip] | None = Field(
        default=None,
        max_length=4,
    )

    @field_validator("allowed_chips")
    @classmethod
    def unique_chips(
        cls,
        chips: list[FPLChip] | None,
    ) -> list[FPLChip] | None:
        if chips is None:
            return chips

        if len(chips) != len(set(chips)):
            raise ValueError(
                "Allowed chips must be unique"
            )

        return chips

    @model_validator(mode="after")
    def at_least_one_rule(
        self,
    ) -> "LeagueRulesUpdate":
        if (
            self.start_gameweek is None
            and self.include_transfer_deductions is None
            and self.allowed_chips is None
        ):
            raise ValueError(
                "At least one league rule must be provided"
            )

        return self

class LeagueUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    rules: LeagueRulesUpdate | None = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    @model_validator(mode="after")
    def at_least_one_update(
        self,
    ) -> "LeagueUpdate":
        if self.name is None and self.rules is None:
            raise ValueError(
                "At least one field must be updated"
            )

        return self
