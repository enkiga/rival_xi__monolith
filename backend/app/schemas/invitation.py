from app.models.league_member import LeagueMemberStatus
from pydantic import BaseModel


class LeagueInvitationLinkResponse(BaseModel):
    league_slug: str
    invitation_url: str


class LeagueInvitationPreviewResponse(BaseModel):
    invitation_id: int

    league_name: str
    league_slug: str

    already_member: bool
    membership_status: LeagueMemberStatus | None
    league_full: bool


class LeagueInvitationAcceptResponse(BaseModel):
    invitation_id: int

    league_id: int
    league_name: str
    league_slug: str

    league_member_id: int
    membership_status: LeagueMemberStatus
