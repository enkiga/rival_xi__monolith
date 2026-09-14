from datetime import datetime

from app.models.league_member import LeagueMemberStatus
from pydantic import BaseModel, Field


class LeagueInvitationCreate(BaseModel):
    expires_in_days: int = Field(
        default=7,
        ge=1,
        le=30,
    )


class LeagueInvitationCreateResponse(BaseModel):
    id: int
    league_slug: str

    # Returned only once when the invitation
    # is created.
    token: str

    expires_at: datetime
    created_at: datetime


class LeagueInvitationResponse(BaseModel):
    id: int
    league_slug: str

    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime

    acceptance_count: int

    active: bool


class LeagueInvitationPreviewResponse(BaseModel):
    invitation_id: int

    league_name: str
    league_slug: str

    expires_at: datetime

    already_member: bool
    membership_status: LeagueMemberStatus | None


class LeagueInvitationAcceptResponse(BaseModel):
    invitation_id: int

    league_id: int
    league_name: str
    league_slug: str

    league_member_id: int
    membership_status: LeagueMemberStatus