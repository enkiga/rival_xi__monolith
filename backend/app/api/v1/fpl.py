from app.api.dependencies.auth import get_current_auth
from app.integrations.fpl.client import FPLUpstreamError
from app.schemas.fpl import (
    FPLGameweekResponse,
    FPLManagerResponse,
)
from app.services.fpl import (
    FPLGameweekNotFoundError,
    FPLPlayerNotFoundError,
    UnsupportedFPLChipError,
    UnsupportedFPLPositionError,
    find_fpl_manager,
    get_fpl_gameweek,
)
from app.services.auth import AuthenticatedSession
from fastapi import APIRouter, Depends, HTTPException, Path, status

router = APIRouter()


@router.get(
    "/teams/{entry_id}",
    response_model=FPLManagerResponse,
)
async def get_fpl_team(
    entry_id: int,
    _auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
) -> FPLManagerResponse:
    try:
        manager = await find_fpl_manager(entry_id)

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )

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
    _auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
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

    except (
        FPLPlayerNotFoundError,
        UnsupportedFPLChipError,
        UnsupportedFPLPositionError,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL returned data that could not be processed",
        )

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )
