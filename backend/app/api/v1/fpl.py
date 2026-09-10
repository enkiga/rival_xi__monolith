from app.schemas.fpl import (
    FPLGameweekResponse,
    FPLManagerResponse,
)
from app.services.fpl import (
    FPLGameweekNotFoundError,
    UnsupportedFPLChipError,
    find_fpl_manager,
    get_fpl_gameweek,
)
from fastapi import APIRouter, HTTPException, Path, status

router = APIRouter()


@router.get(
    "/teams/{entry_id}",
    response_model=FPLManagerResponse,
)
async def get_fpl_team(
    entry_id: int,
) -> FPLManagerResponse:
    manager = await find_fpl_manager(entry_id)

    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FPL team not found",
        )

    return manager

@router.get(
    "/teams/{entry_id}/gameweeks/{gameweek}",
    response_model=FPLGameweekResponse,
)
async def get_fpl_gameweek_endpoint(
    entry_id: int,
    gameweek: int = Path(
        ge=1,
        le=38,
    ),
) -> FPLGameweekResponse:
    try:
        return await get_fpl_gameweek(
            entry_id=entry_id,
            gameweek=gameweek,
        )

    except FPLGameweekNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FPL gameweek data not found",
        )

    except UnsupportedFPLChipError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL returned an unsupported chip",
        )