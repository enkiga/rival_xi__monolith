import hashlib
import hmac
import secrets

from app.core.config import settings


def normalize_email(
    email: str,
) -> str:
    return email.strip().casefold()


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(
    email: str,
    code: str,
) -> str:
    message = (f"{normalize_email(email)}:{code}").encode()

    return hmac.new(
        settings.auth_otp_secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def verify_otp(
    email: str,
    code: str,
    expected_hash: str,
) -> bool:
    candidate_hash = hash_otp(
        email=email,
        code=code,
    )

    return hmac.compare_digest(
        candidate_hash,
        expected_hash,
    )


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(
    token: str,
) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
