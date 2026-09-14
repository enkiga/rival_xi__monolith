from datetime import datetime

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class OTPRequest(BaseModel):
    email: EmailStr


class OTPRequestResponse(BaseModel):
    message: str
    expires_in_seconds: int


class OTPVerifyRequest(BaseModel):
    email: EmailStr

    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class FPLAccountSummary(BaseModel):
    fpl_entry_id: int
    team_name: str
    manager_name: str


class AuthUserResponse(BaseModel):
    id: int
    email: str
    email_verified_at: datetime

    onboarding_required: bool

    fpl_account: FPLAccountSummary | None


class OTPVerifyResponse(BaseModel):
    user: AuthUserResponse


class LogoutRequest(BaseModel):
    all_sessions: bool = False


class LogoutResponse(BaseModel):
    message: str
    all_sessions_cleared: bool
