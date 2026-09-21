from typing import Literal

from app.api.dependencies.auth import get_current_auth
from app.db.session import get_db
from app.integrations.fpl.client import FPLUpstreamError
from app.schemas.gameweek import (
    LeagueGameweekResponse,
    LeagueGameweekSummaryResponse,
    LeagueGameweekSyncResponse,
    MemberGameweekResponse,
)
from app.schemas.league import (
    LeagueCreate,
    LeagueDetailResponse,
    LeagueListResponse,
    LeagueMemberResponse,
    LeagueResponse,
    LeagueStatusResponse,
    LeagueUpdate,
)
from app.services.auth import AuthenticatedSession
from app.services.fpl import CurrentGameweekNotFoundError
from app.services.gameweek import (
    FutureGameweekError,
    GameweekBeforeLeagueStartError,
    GameweekEventNotFoundError,
    GameweekLeagueNotFoundError,
    GameweekMemberResultNotFoundError,
    GameweekResultsNotFoundError,
    GameweekSyncDataError,
    GameweekSyncOwnerRequiredError,
    LeagueNotActiveError,
    get_league_gameweek,
    get_league_gameweek_summary,
    get_member_gameweek,
    sync_league_gameweek_as_owner,
)
from app.services.league import (
    CannotManageOwnerError,
    DuplicateLeagueError,
    FPLAccountRequiredError,
    InvalidMemberStatusError,
    LeagueAlreadyActiveError,
    LeagueEditingClosedError,
    LeagueFullError,
    LeagueMemberNotFoundError,
    LeagueNotFoundError,
    LeagueOwnerRequiredError,
    activate_league,
    approve_league_member,
    create_league,
    get_league,
    get_user_leagues,
    reject_league_member,
    update_league,
)
from app.services.league_access import (
    LeagueMembershipPendingError,
    LeagueMembershipRequiredError,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _raise_league_access_error(
    exc: Exception,
) -> None:
    if isinstance(exc, LeagueMembershipPendingError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your league membership is awaiting approval",
        )

    if isinstance(exc, LeagueMembershipRequiredError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approved league membership is required",
        )

    raise exc


@router.post(
    "",
    response_model=LeagueResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_league_endpoint(
    data: LeagueCreate,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueResponse:
    try:
        return await create_league(
            db=db,
            data=data,
            user_id=auth.user_id,
        )

    except FPLAccountRequiredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Link an FPL account before creating or joining a league",
        )

    except DuplicateLeagueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="League with the same name already exists",
        )


@router.get(
    "",
    response_model=LeagueListResponse,
)
async def get_leagues_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
    sort_by: Literal["name", "created_at"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueListResponse:
    return await get_user_leagues(
        db=db,
        user_id=auth.user_id,
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{slug}",
    response_model=LeagueDetailResponse,
)
async def get_league_endpoint(
    slug: str,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueDetailResponse:
    try:
        return await get_league(
            db=db,
            slug=slug,
            user_id=auth.user_id,
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except (
        LeagueMembershipPendingError,
        LeagueMembershipRequiredError,
    ) as exc:
        _raise_league_access_error(exc)

        raise

    except (
        CurrentGameweekNotFoundError,
        FPLUpstreamError,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to determine the current FPL gameweek",
        )


@router.patch(
    "/{slug}/members/{member_id}/approve",
    response_model=LeagueMemberResponse,
)
async def approve_member_endpoint(
    slug: str,
    member_id: int,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueMemberResponse:
    try:
        return await approve_league_member(
            db=db,
            slug=slug,
            member_id=member_id,
            owner_user_id=auth.user_id,
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except LeagueMemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League member not found",
        )

    except LeagueOwnerRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can approve members",
        )

    except LeagueFullError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="League has reached the 20-member limit",
        )

    except (
        InvalidMemberStatusError,
        CannotManageOwnerError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member cannot be approved",
        )

    except (
        CurrentGameweekNotFoundError,
        FPLUpstreamError,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to determine the current FPL gameweek",
        )


@router.patch(
    "/{slug}/members/{member_id}/reject",
    response_model=LeagueMemberResponse,
)
async def reject_member_endpoint(
    slug: str,
    member_id: int,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueMemberResponse:
    try:
        return await reject_league_member(
            db=db,
            slug=slug,
            member_id=member_id,
            owner_user_id=auth.user_id,
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except LeagueMemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League member not found",
        )

    except LeagueOwnerRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can reject members",
        )

    except (
        InvalidMemberStatusError,
        CannotManageOwnerError,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Member cannot be rejected",
        )


@router.patch(
    "/{slug}/activate",
    response_model=LeagueStatusResponse,
)
async def activate_league_endpoint(
    slug: str,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueStatusResponse:
    try:
        return await activate_league(
            db=db,
            slug=slug,
            owner_user_id=auth.user_id,
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except LeagueOwnerRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can activate the league",
        )

    except LeagueAlreadyActiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="League is already active",
        )


@router.patch(
    "/{slug}",
    response_model=LeagueDetailResponse,
)
async def update_league_endpoint(
    slug: str,
    data: LeagueUpdate,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueDetailResponse:
    try:
        return await update_league(
            db=db,
            slug=slug,
            data=data,
            owner_user_id=auth.user_id,
        )

    except LeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except LeagueOwnerRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can edit the league",
        )

    except DuplicateLeagueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A league with this name already exists",
        )

    except LeagueEditingClosedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active league configuration cannot be edited",
        )

    except (
        CurrentGameweekNotFoundError,
        FPLUpstreamError,
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to determine the current FPL gameweek",
        )


@router.post(
    "/{slug}/gameweeks/{gameweek}/sync",
    response_model=LeagueGameweekSyncResponse,
)
async def sync_gameweek_endpoint(
    slug: str,
    gameweek: int,
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueGameweekSyncResponse:
    if gameweek < 1 or gameweek > 38:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Gameweek must be between 1 and 38",
        )

    try:
        return await sync_league_gameweek_as_owner(
            db=db,
            slug=slug,
            gameweek=gameweek,
            owner_user_id=auth.user_id,
        )

    except GameweekLeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except GameweekSyncOwnerRequiredError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the league owner can sync gameweek results",
        )

    except LeagueNotActiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="League is not active",
        )

    except GameweekBeforeLeagueStartError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek is before the league start gameweek",
        )

    except FutureGameweekError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek has not started yet",
        )

    except GameweekEventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FPL gameweek not found",
        )

    except GameweekSyncDataError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve complete FPL gameweek data",
        )

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )


@router.get(
    "/{slug}/gameweeks/{gameweek}/summary",
    response_model=LeagueGameweekSummaryResponse,
)
async def get_league_gameweek_summary_endpoint(
    slug: str,
    gameweek: int = Path(
        ge=1,
        le=38,
    ),
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueGameweekSummaryResponse:
    try:
        return await get_league_gameweek_summary(
            db=db,
            slug=slug,
            gameweek=gameweek,
            user_id=auth.user_id,
        )

    except GameweekLeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except (
        LeagueMembershipPendingError,
        LeagueMembershipRequiredError,
    ) as exc:
        _raise_league_access_error(exc)

        raise

    except GameweekBeforeLeagueStartError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek is before the league start gameweek",
        )

    except FutureGameweekError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek has not started yet",
        )

    except GameweekEventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FPL gameweek not found",
        )

    except GameweekResultsNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek results are not available",
        )

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )


@router.get(
    "/{slug}/gameweeks/{gameweek}",
    response_model=LeagueGameweekResponse,
)
async def get_league_gameweek_endpoint(
    slug: str,
    gameweek: int = Path(
        ge=1,
        le=38,
    ),
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LeagueGameweekResponse:
    try:
        return await get_league_gameweek(
            db=db,
            slug=slug,
            gameweek=gameweek,
            user_id=auth.user_id,
        )

    except GameweekLeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except (
        LeagueMembershipPendingError,
        LeagueMembershipRequiredError,
    ) as exc:
        _raise_league_access_error(exc)

        raise

    except GameweekBeforeLeagueStartError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek is before the league start gameweek",
        )

    except FutureGameweekError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek has not started yet",
        )

    except GameweekEventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FPL gameweek not found",
        )

    except GameweekResultsNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek results are not available",
        )

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )


@router.get(
    "/{slug}/gameweeks/{gameweek}/members/{member_id}",
    response_model=MemberGameweekResponse,
)
async def get_member_gameweek_endpoint(
    slug: str,
    member_id: int,
    gameweek: int = Path(
        ge=1,
        le=38,
    ),
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> MemberGameweekResponse:
    try:
        return await get_member_gameweek(
            db=db,
            slug=slug,
            gameweek=gameweek,
            member_id=member_id,
            user_id=auth.user_id,
        )

    except GameweekLeagueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="League not found",
        )

    except (
        LeagueMembershipPendingError,
        LeagueMembershipRequiredError,
    ) as exc:
        _raise_league_access_error(exc)

        raise

    except FutureGameweekError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek has not started yet",
        )

    except GameweekEventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FPL gameweek not found",
        )

    except GameweekResultsNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameweek results are not available",
        )

    except GameweekMemberResultNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member has no result for this gameweek",
        )

    except GameweekBeforeLeagueStartError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Gameweek is before the league start gameweek",
        )

    except FPLUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FPL service is temporarily unavailable",
        )
