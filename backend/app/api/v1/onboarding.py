from app.api.dependencies.auth import (
    get_current_auth,
)
from app.db.session import get_db
from app.integrations.fpl.client import FPLUpstreamError
from app.schemas.onboarding import (
    FPLTeamClaimRequest,
    FPLTeamClaimResponse,
    FPLTeamLookupRequest,
    FPLTeamPreviewResponse,
)
from app.services.auth import (
    AuthenticatedSession,
)
from app.services.onboarding import (
    FPLAccountAlreadyLinkedError,
    FPLAccountClaimConflictError,
    FPLAccountTakenError,
    FPLTeamNotFoundError,
    InvalidFPLReferenceError,
    claim_fpl_team,
    preview_fpl_team,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

router = APIRouter()


@router.post(
    "/fpl/preview",
    response_model=(FPLTeamPreviewResponse),
)
async def preview_fpl_team_endpoint(
    data: FPLTeamLookupRequest,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(  # noqa: B008
        get_db
    ),
) -> FPLTeamPreviewResponse:
    try:
        return await preview_fpl_team(
            db=db,
            user_id=auth.user_id,
            reference=data.reference,
        )

    except InvalidFPLReferenceError:
        raise HTTPException(
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=("Enter a valid FPL team URL or entry ID"),
        )

    except FPLTeamNotFoundError:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="FPL team not found",
        )

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )


@router.post(
    "/fpl/claim",
    response_model=(FPLTeamClaimResponse),
)
async def claim_fpl_team_endpoint(
    data: FPLTeamClaimRequest,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(  # noqa: B008
        get_db
    ),
) -> FPLTeamClaimResponse:
    try:
        return await claim_fpl_team(
            db=db,
            user_id=auth.user_id,
            reference=data.reference,
        )

    except InvalidFPLReferenceError:
        raise HTTPException(
            status_code=(status.HTTP_422_UNPROCESSABLE_ENTITY),
            detail=("Enter a valid FPL team URL or entry ID"),
        )

    except FPLTeamNotFoundError:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="FPL team not found",
        )

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )

    except FPLAccountTakenError:
        raise HTTPException(
            status_code=(status.HTTP_409_CONFLICT),
            detail=("This FPL team is already linked to another Rivalxi account"),
        )

    except FPLAccountAlreadyLinkedError:
        raise HTTPException(
            status_code=(status.HTTP_409_CONFLICT),
            detail=("Your Rivalxi account is already linked to an FPL team"),
        )

    except FPLAccountClaimConflictError:
        raise HTTPException(
            status_code=(status.HTTP_409_CONFLICT),
            detail=("The FPL team could not be claimed. Please try again."),
        )
