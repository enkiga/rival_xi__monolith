from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.auth import (
    AuthenticatedSession,
    SessionNotFoundError,
    get_authenticated_session,
)
from fastapi import (
    HTTPException,
    Request,
    status,
)


async def get_current_auth(
    request: Request,
) -> AuthenticatedSession:
    session_token = (
        request.cookies.get(
            settings
            .auth_session_cookie_name
        )
    )

    if session_token is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Authentication required",
        )

    # Deliberately use a separate session here.
    #
    # Protected endpoint services often open their
    # own explicit db.begin() transactions. Sharing
    # this read session would trigger SQLAlchemy
    # autobegin and interfere with them.
    async with AsyncSessionLocal() as db:
        try:
            return (
                await get_authenticated_session(
                    db=db,
                    session_token=(
                        session_token
                    ),
                )
            )

        except SessionNotFoundError:
            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail=(
                    "Session is invalid "
                    "or expired"
                ),
            )