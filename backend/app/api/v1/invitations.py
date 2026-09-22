from app.api.dependencies.auth import get_current_auth
from app.db.session import get_db
from app.schemas.invitation import (
    LeagueInvitationAcceptResponse,
    LeagueInvitationLinkResponse,
    LeagueInvitationPreviewResponse,
)
from app.services.auth import AuthenticatedSession
from app.services.invitation import (
    InvitationNotFoundError,
    InvitationOwnerRequiredError,
    InvitationRevokedError,
    accept_league_invitation,
    get_league_invitation_link,
    preview_league_invitation,
    regenerate_league_invitation_link,
)
from app.services.league import (
    FPLAccountRequiredError,
    LeagueFullError,
    LeagueNotFoundError,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _raise_owner_link_error(exc: Exception) -> None:
    if isinstance(exc, LeagueNotFoundError):
        raise HTTPException(status_code=404, detail="League not found")
    if isinstance(exc, InvitationNotFoundError):
        raise HTTPException(status_code=404, detail="Invitation link not found")
    if isinstance(exc, InvitationOwnerRequiredError):
        raise HTTPException(
            status_code=403,
            detail="Only the league owner can manage the invitation link",
        )
    raise exc


@router.get(
    "/leagues/{slug}/invitation-link",
    response_model=LeagueInvitationLinkResponse,
)
async def get_invitation_link_endpoint(
    slug: str,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueInvitationLinkResponse:
    try:
        return await get_league_invitation_link(
            db=db, slug=slug, user_id=auth.user_id
        )
    except (
        LeagueNotFoundError,
        InvitationNotFoundError,
        InvitationOwnerRequiredError,
    ) as exc:
        _raise_owner_link_error(exc)
        raise


@router.post(
    "/leagues/{slug}/invitation-link/regenerate",
    response_model=LeagueInvitationLinkResponse,
)
async def regenerate_invitation_link_endpoint(
    slug: str,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueInvitationLinkResponse:
    try:
        return await regenerate_league_invitation_link(
            db=db, slug=slug, user_id=auth.user_id
        )
    except (
        LeagueNotFoundError,
        InvitationNotFoundError,
        InvitationOwnerRequiredError,
    ) as exc:
        _raise_owner_link_error(exc)
        raise


def _raise_invitation_error(exc: Exception) -> None:
    if isinstance(exc, InvitationNotFoundError):
        raise HTTPException(status_code=404, detail="Invitation not found")
    if isinstance(exc, InvitationRevokedError):
        raise HTTPException(status_code=410, detail="Invitation has been revoked")
    raise exc


@router.get(
    "/invitations/{token}",
    response_model=LeagueInvitationPreviewResponse,
)
async def preview_invitation_endpoint(
    token: str,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueInvitationPreviewResponse:
    try:
        return await preview_league_invitation(
            db=db, token=token, user_id=auth.user_id
        )
    except (InvitationNotFoundError, InvitationRevokedError) as exc:
        _raise_invitation_error(exc)
        raise


@router.post(
    "/invitations/{token}/accept",
    response_model=LeagueInvitationAcceptResponse,
)
async def accept_invitation_endpoint(
    token: str,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueInvitationAcceptResponse:
    try:
        return await accept_league_invitation(
            db=db, token=token, user_id=auth.user_id
        )
    except (InvitationNotFoundError, InvitationRevokedError) as exc:
        _raise_invitation_error(exc)
        raise
    except FPLAccountRequiredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete FPL onboarding before accepting an invitation",
        )
    except LeagueFullError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This league has reached its member limit",
        )
    except LeagueNotFoundError:
        raise HTTPException(status_code=404, detail="League not found")
