from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from math import ceil

from app.core.auth_security import (
    generate_otp,
    generate_session_token,
    hash_otp,
    hash_session_token,
    normalize_email,
    verify_otp,
)
from app.core.config import settings
from app.core.rate_limit import (
    enforce_rate_limit,
)
from app.integrations.email.client import (
    EmailDeliveryError,
    send_auth_otp_email,
)
from app.models.auth_challenge import (
    AuthChallenge,
)
from app.models.fpl_account import (
    FPLAccount,
)
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import (
    AuthUserResponse,
    FPLAccountSummary,
)
from sqlalchemy import (
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession


class InvalidOTPError(Exception):
    pass


class OTPExpiredError(Exception):
    pass


class OTPAttemptsExceededError(Exception):
    pass


class OTPResendCooldownError(Exception):
    def __init__(
        self,
        retry_after: int,
    ):
        self.retry_after = retry_after

        super().__init__(
            "OTP resend cooldown active"
        )


class SessionNotFoundError(Exception):
    pass


class AuthUserNotFoundError(Exception):
    pass


class AuthEmailDeliveryError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticatedSession:
    user_id: int
    session_id: int
    email: str
    email_verified_at: datetime


@dataclass(frozen=True)
class AuthVerificationResult:
    user: AuthUserResponse
    session_token: str


async def _build_auth_user_response(
    db: AsyncSession,
    user: User,
) -> AuthUserResponse:
    fpl_account = await db.scalar(
        select(FPLAccount).where(
            FPLAccount.user_id == user.id,
        )
    )

    fpl_summary = None

    if fpl_account is not None:
        fpl_summary = FPLAccountSummary(
            fpl_entry_id=(
                fpl_account.fpl_entry_id
            ),
            team_name=(
                fpl_account.team_name
            ),
            manager_name=(
                fpl_account.manager_name
            ),
        )

    return AuthUserResponse(
        id=user.id,
        email=user.email,
        email_verified_at=(
            user.email_verified_at
        ),
        onboarding_required=(
            fpl_account is None
        ),
        fpl_account=fpl_summary,
    )


async def request_auth_otp(
    db: AsyncSession,
    email: str,
    client_ip: str,
) -> None:
    email = normalize_email(email)

    await enforce_rate_limit(
        scope="auth:otp-request:email",
        identifier=email,
        limit=(
            settings
            .auth_otp_request_email_limit
        ),
        window_seconds=(
            settings
            .auth_rate_limit_window_seconds
        ),
    )

    await enforce_rate_limit(
        scope="auth:otp-request:ip",
        identifier=client_ip,
        limit=(
            settings
            .auth_otp_request_ip_limit
        ),
        window_seconds=(
            settings
            .auth_rate_limit_window_seconds
        ),
    )

    now = datetime.now(
        timezone.utc
    )

    code = generate_otp()

    challenge_id: int

    async with db.begin():
        latest_challenge = await db.scalar(
            select(AuthChallenge)
            .where(
                AuthChallenge.email == email,
                AuthChallenge.used_at.is_(
                    None
                ),
            )
            .order_by(
                AuthChallenge.created_at.desc()
            )
            .limit(1)
            .with_for_update()
        )

        if latest_challenge is not None:
            cooldown_until = (
                latest_challenge.created_at
                + timedelta(
                    seconds=(
                        settings
                        .auth_otp_resend_cooldown_seconds
                    )
                )
            )

            if now < cooldown_until:
                retry_after = ceil(
                    (
                        cooldown_until
                        - now
                    ).total_seconds()
                )

                raise OTPResendCooldownError(
                    retry_after=retry_after
                )

        # Invalidate previous unused codes.
        await db.execute(
            update(AuthChallenge)
            .where(
                AuthChallenge.email == email,
                AuthChallenge.used_at.is_(
                    None
                ),
            )
            .values(
                used_at=now
            )
        )

        challenge = AuthChallenge(
            email=email,
            code_hash=hash_otp(
                email=email,
                code=code,
            ),
            attempts=0,
            expires_at=(
                now
                + timedelta(
                    minutes=(
                        settings
                        .auth_otp_ttl_minutes
                    )
                )
            ),
        )

        db.add(challenge)

        await db.flush()

        challenge_id = challenge.id

    # Email is external I/O, so don't hold a
    # database transaction while sending it.
    try:
        await send_auth_otp_email(
            email=email,
            code=code,
            expires_in_minutes=(
                settings.auth_otp_ttl_minutes
            ),
        )

    except EmailDeliveryError as exc:
        # The challenge must not remain usable if
        # the email was never delivered.
        async with db.begin():
            challenge = await db.scalar(
                select(AuthChallenge)
                .where(
                    AuthChallenge.id
                    == challenge_id
                )
                .with_for_update()
            )

            if challenge is not None:
                challenge.used_at = (
                    datetime.now(
                        timezone.utc
                    )
                )

        raise AuthEmailDeliveryError from exc


async def verify_auth_otp(
    db: AsyncSession,
    email: str,
    code: str,
    client_ip: str,
) -> AuthVerificationResult:
    email = normalize_email(email)

    await enforce_rate_limit(
        scope="auth:otp-verify:email",
        identifier=email,
        limit=(
            settings
            .auth_otp_verify_email_limit
        ),
        window_seconds=(
            settings
            .auth_rate_limit_window_seconds
        ),
    )

    await enforce_rate_limit(
        scope="auth:otp-verify:ip",
        identifier=client_ip,
        limit=(
            settings
            .auth_otp_verify_ip_limit
        ),
        window_seconds=(
            settings
            .auth_rate_limit_window_seconds
        ),
    )

    now = datetime.now(
        timezone.utc
    )

    failure: Exception | None = None

    session_token: str | None = None
    user_response: (
        AuthUserResponse | None
    ) = None

    async with db.begin():
        challenge = await db.scalar(
            select(AuthChallenge)
            .where(
                AuthChallenge.email == email,
                AuthChallenge.used_at.is_(
                    None
                ),
            )
            .order_by(
                AuthChallenge.created_at.desc()
            )
            .limit(1)
            .with_for_update()
        )

        if challenge is None:
            failure = InvalidOTPError()

        elif challenge.expires_at <= now:
            challenge.used_at = now

            failure = OTPExpiredError()

        elif (
            challenge.attempts
            >= settings.auth_otp_max_attempts
        ):
            challenge.used_at = now

            failure = (
                OTPAttemptsExceededError()
            )

        elif not verify_otp(
            email=email,
            code=code,
            expected_hash=(
                challenge.code_hash
            ),
        ):
            challenge.attempts += 1

            if (
                challenge.attempts
                >= settings
                .auth_otp_max_attempts
            ):
                challenge.used_at = now

                failure = (
                    OTPAttemptsExceededError()
                )

            else:
                failure = InvalidOTPError()

        else:
            challenge.used_at = now

            user = await db.scalar(
                select(User).where(
                    User.email == email,
                )
            )

            if user is None:
                user = User(
                    email=email,
                    email_verified_at=now,
                )

                db.add(user)

                await db.flush()

            session_token = (
                generate_session_token()
            )

            session = Session(
                user_id=user.id,
                token_hash=(
                    hash_session_token(
                        session_token
                    )
                ),
                expires_at=(
                    now
                    + timedelta(
                        days=(
                            settings
                            .auth_session_ttl_days
                        )
                    )
                ),
            )

            db.add(session)

            await db.flush()

            user_response = (
                await _build_auth_user_response(
                    db=db,
                    user=user,
                )
            )

    # Raising after the transaction allows failed
    # attempt counters / expiration state to commit.
    if failure is not None:
        raise failure

    if (
        session_token is None
        or user_response is None
    ):
        raise InvalidOTPError

    return AuthVerificationResult(
        user=user_response,
        session_token=session_token,
    )


async def get_authenticated_session(
    db: AsyncSession,
    session_token: str,
) -> AuthenticatedSession:
    now = datetime.now(
        timezone.utc
    )

    token_hash = hash_session_token(
        session_token
    )

    result = await db.execute(
        select(
            Session,
            User,
        )
        .join(
            User,
            User.id == Session.user_id,
        )
        .where(
            Session.token_hash
            == token_hash,
            Session.revoked_at.is_(None),
            Session.expires_at > now,
        )
    )

    row = result.first()

    if row is None:
        raise SessionNotFoundError

    session, user = row

    return AuthenticatedSession(
        user_id=user.id,
        session_id=session.id,
        email=user.email,
        email_verified_at=(
            user.email_verified_at
        ),
    )


async def get_auth_user_response(
    db: AsyncSession,
    user_id: int,
) -> AuthUserResponse:
    user = await db.scalar(
        select(User).where(
            User.id == user_id,
        )
    )

    if user is None:
        raise AuthUserNotFoundError

    return await _build_auth_user_response(
        db=db,
        user=user,
    )


async def logout_session(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: int,
    all_sessions: bool,
) -> None:
    now = datetime.now(
        timezone.utc
    )

    async with db.begin():
        if all_sessions:
            await db.execute(
                update(Session)
                .where(
                    Session.user_id
                    == user_id,
                    Session.revoked_at.is_(
                        None
                    ),
                )
                .values(
                    revoked_at=now
                )
            )

            return

        result = await db.execute(
            update(Session)
            .where(
                Session.id == session_id,
                Session.user_id
                == user_id,
                Session.revoked_at.is_(
                    None
                ),
            )
            .values(
                revoked_at=now
            )
        )

        if result.rowcount == 0:
            raise SessionNotFoundError