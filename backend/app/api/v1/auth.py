from app.api.dependencies.auth import get_current_auth
from app.core.config import settings
from app.core.rate_limit import (
    RateLimitExceededError,
    RateLimitUnavailableError,
)
from app.db.session import get_db
from app.schemas.auth import (
    AuthUserResponse,
    LogoutRequest,
    LogoutResponse,
    OTPRequest,
    OTPRequestResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
)
from app.services.auth import (
    AuthEmailDeliveryError,
    AuthenticatedSession,
    AuthUserNotFoundError,
    InvalidOTPError,
    OTPAttemptsExceededError,
    OTPExpiredError,
    OTPResendCooldownError,
    SessionNotFoundError,
    get_auth_user_response,
    logout_session,
    request_auth_otp,
    verify_auth_otp,
)
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

router = APIRouter()


def _get_client_ip(
    request: Request,
) -> str:
    if request.client is None:
        return "unknown"

    return request.client.host


@router.post(
    "/otp/request",
    response_model=OTPRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_otp_endpoint(
    data: OTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> OTPRequestResponse:
    try:
        await request_auth_otp(
            db=db,
            email=str(data.email),
            client_ip=_get_client_ip(request),
        )

    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Too many OTP requests. Please try again later."),
            headers={"Retry-After": str(exc.retry_after)},
        )

    except RateLimitUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication rate limiting is unavailable",
        )

    except OTPResendCooldownError as exc:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Please wait before requesting another code."),
            headers={"Retry-After": str(exc.retry_after)},
        )

    except AuthEmailDeliveryError:
        raise HTTPException(
            status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
            detail=("Unable to send verification email"),
        )

    return OTPRequestResponse(
        message=("If the email address is valid, a verification code has been sent."),
        expires_in_seconds=(settings.auth_otp_ttl_minutes * 60),
    )


@router.post(
    "/otp/verify",
    response_model=OTPVerifyResponse,
)
async def verify_otp_endpoint(
    data: OTPVerifyRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> OTPVerifyResponse:
    try:
        result = await verify_auth_otp(
            db=db,
            email=str(data.email),
            code=data.code,
            client_ip=_get_client_ip(request),
        )

    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Too many verification attempts. Try again later."),
            headers={"Retry-After": str(exc.retry_after)},
        )

    except RateLimitUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication rate limiting is unavailable",
        )

    except OTPAttemptsExceededError:
        raise HTTPException(
            status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
            detail=("Maximum verification attempts exceeded. Request a new code."),
        )

    except OTPExpiredError:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail=("Verification code has expired"),
        )

    except InvalidOTPError:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid verification code",
        )

    response.set_cookie(
        key=(settings.auth_session_cookie_name),
        value=result.session_token,
        max_age=(settings.auth_session_ttl_days * 24 * 60 * 60),
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )

    return OTPVerifyResponse(
        user=result.user,
    )


@router.get(
    "/me",
    response_model=AuthUserResponse,
)
async def get_me_endpoint(
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AuthUserResponse:
    try:
        return await get_auth_user_response(
            db=db,
            user_id=auth.user_id,
        )

    except AuthUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid",
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout_endpoint(
    data: LogoutRequest,
    response: Response,
    auth: AuthenticatedSession = Depends(  # noqa: B008
        get_current_auth
    ),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> LogoutResponse:
    try:
        await logout_session(
            db=db,
            user_id=auth.user_id,
            session_id=auth.session_id,
            all_sessions=(data.all_sessions),
        )

    except SessionNotFoundError:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Session is invalid",
        )

    response.delete_cookie(
        key=(settings.auth_session_cookie_name),
        path="/",
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite="lax",
    )

    if data.all_sessions:
        return LogoutResponse(
            message=("Signed out from all devices"),
            all_sessions_cleared=True,
        )

    return LogoutResponse(
        message="Signed out",
        all_sessions_cleared=False,
    )
