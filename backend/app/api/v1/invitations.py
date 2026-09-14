from app.api.dependencies.auth import (
    get_current_auth,
)
from app.db.session import get_db
from app.schemas.invitation import (
    LeagueInvitationAcceptResponse,
    LeagueInvitationCreate,
    LeagueInvitationCreateResponse,
    LeagueInvitationPreviewResponse,
    LeagueInvitationResponse,
)
from app.services.auth import (
    AuthenticatedSession,
)
from app.services.invitation import (
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationOwnerRequiredError,
    InvitationRevokedError,
    accept_league_invitation,
    create_league_invitation,
    list_league_invitations,
    preview_league_invitation,
    revoke_league_invitation,
)
from app.services.league import (
    FPLAccountRequiredError,
    LeagueFullError,
    LeagueNotFoundError,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post(
    "/leagues/{slug}/invitations",
    response_model=(
        LeagueInvitationCreateResponse
    ),
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation_endpoint(
    slug: str,
    data: LeagueInvitationCreate,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueInvitationCreateResponse:
    try:
        return await create_league_invitation(
            db=db,
            slug=slug,
            user_id=auth.user_id,
            expires_in_days=(
                data.expires_in_days
            ),
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="League not found",
        )

    except InvitationOwnerRequiredError:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the league owner can "
                "create invitations"
            ),
        )

@router.get(
    "/leagues/{slug}/invitations",
    response_model=list[
        LeagueInvitationResponse
    ],
)
async def list_invitations_endpoint(
    slug: str,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[LeagueInvitationResponse]:
    try:
        return await list_league_invitations(
            db=db,
            slug=slug,
            user_id=auth.user_id,
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="League not found",
        )

    except InvitationOwnerRequiredError:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the league owner can "
                "view invitations"
            ),
        )

@router.delete(
    "/leagues/{slug}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_invitation_endpoint(
    slug: str,
    invitation_id: int,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Response:
    try:
        await revoke_league_invitation(
            db=db,
            slug=slug,
            invitation_id=invitation_id,
            user_id=auth.user_id,
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="League not found",
        )

    except InvitationNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Invitation not found",
        )

    except InvitationOwnerRequiredError:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only the league owner can "
                "revoke invitations"
            ),
        )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )

def _raise_invitation_error(
    exc: Exception,
) -> None:
    if isinstance(
        exc,
        InvitationNotFoundError,
    ):
        raise HTTPException(
            status_code=404,
            detail="Invitation not found",
        )

    if isinstance(
        exc,
        InvitationExpiredError,
    ):
        raise HTTPException(
            status_code=410,
            detail="Invitation has expired",
        )

    if isinstance(
        exc,
        InvitationRevokedError,
    ):
        raise HTTPException(
            status_code=410,
            detail="Invitation has been revoked",
        )

    raise exc

@router.get(
    "/invitations/{token}",
    response_model=(
        LeagueInvitationPreviewResponse
    ),
)
async def preview_invitation_endpoint(
    token: str,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueInvitationPreviewResponse:
    try:
        return await preview_league_invitation(
            db=db,
            token=token,
            user_id=auth.user_id,
        )

    except (
        InvitationNotFoundError,
        InvitationExpiredError,
        InvitationRevokedError,
    ) as exc:
        _raise_invitation_error(exc)

        raise

@router.post(
    "/invitations/{token}/accept",
    response_model=(
        LeagueInvitationAcceptResponse
    ),
)
async def accept_invitation_endpoint(
    token: str,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueInvitationAcceptResponse:
    try:
        return await accept_league_invitation(
            db=db,
            token=token,
            user_id=auth.user_id,
        )

    except (
        InvitationNotFoundError,
        InvitationExpiredError,
        InvitationRevokedError,
    ) as exc:
        _raise_invitation_error(exc)

        raise

    except FPLAccountRequiredError:
        raise HTTPException(
            status_code=409,
            detail=(
                "Complete FPL onboarding "
                "before accepting an invitation"
            ),
        )

    except LeagueFullError:
        raise HTTPException(
            status_code=409,
            detail=(
                "This league has reached "
                "its member limit"
            ),
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="League not found",
        )