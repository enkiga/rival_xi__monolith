from app.api.dependencies.auth import (
    get_current_auth,
)
from app.db.session import get_db
from app.schemas.notification import (
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.auth import (
    AuthenticatedSession,
)
from app.services.notification import (
    NotificationNotFoundError,
    get_unread_notification_count,
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

router = APIRouter()


@router.get(
    "",
    response_model=NotificationListResponse,
)
async def get_notifications_endpoint(
    unread_only: bool = False,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> NotificationListResponse:
    return await get_user_notifications(
        db=db,
        user_id=auth.user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )


@router.get(
    "/unread-count",
    response_model=(NotificationUnreadCountResponse),
)
async def get_unread_count_endpoint(
    auth: AuthenticatedSession = Depends(get_current_auth),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> NotificationUnreadCountResponse:
    count = await get_unread_notification_count(
        db=db,
        user_id=auth.user_id,
    )

    return NotificationUnreadCountResponse(unread_count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_notification_read_endpoint(
    notification_id: int,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(  # noqa: B008
        get_db
    ),
) -> NotificationResponse:
    try:
        return await mark_notification_read(
            db=db,
            user_id=auth.user_id,
            notification_id=(notification_id),
        )

    except NotificationNotFoundError:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="Notification not found",
        )


@router.patch(
    "/read-all",
    response_model=(NotificationReadAllResponse),
)
async def mark_all_read_endpoint(
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(  # noqa: B008
        get_db
    ),
) -> NotificationReadAllResponse:
    updated_count = await mark_all_notifications_read(
        db=db,
        user_id=auth.user_id,
    )

    return NotificationReadAllResponse(updated_count=updated_count)
