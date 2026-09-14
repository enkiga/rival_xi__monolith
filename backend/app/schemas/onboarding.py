from pydantic import (
    BaseModel,
    Field,
)


class FPLTeamLookupRequest(BaseModel):
    reference: str = Field(
        min_length=1,
        max_length=500,
    )


class FPLTeamPreviewResponse(BaseModel):
    fpl_entry_id: int

    team_name: str
    manager_name: str

    available: bool
    linked_to_current_user: bool


class FPLTeamClaimRequest(BaseModel):
    reference: str = Field(
        min_length=1,
        max_length=500,
    )


class FPLTeamClaimResponse(BaseModel):
    fpl_entry_id: int
    team_name: str
    manager_name: str

    onboarding_required: bool = False
