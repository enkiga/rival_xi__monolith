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

    overall_points: int | None = None
    overall_rank: int | None = None


class FPLManagerSearchResult(BaseModel):
    entry_id: int = Field(gt=0)
    manager_name: str = Field(min_length=1, max_length=150)
    team_name: str = Field(min_length=1, max_length=100)


class FPLManagerSearchResponse(BaseModel):
    results: list[FPLManagerSearchResult]
    search_available: bool = True


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
