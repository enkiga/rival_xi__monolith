from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    auth_otp_secret: str

    gameweek_sync_interval_minutes: int

    # Outbound FPL protection.
    fpl_request_interval_ms: int = 2000
    fpl_max_retries: int = 3

    # FPL cache.
    fpl_bootstrap_cache_ttl: int = 300
    fpl_entry_cache_ttl: int = 600
    fpl_live_cache_ttl: int = 120
    fpl_picks_cache_ttl: int = 120

    # Rivalxi response cache.
    live_gameweek_cache_ttl: int = 30
    final_gameweek_cache_ttl: int = 86400

    auth_otp_ttl_minutes: int = 10
    auth_otp_max_attempts: int = 5
    auth_otp_resend_cooldown_seconds: int = 60

    auth_session_ttl_days: int = 30
    auth_session_cookie_name: str = "rivalxi_session"
    auth_cookie_secure: bool = True

    auth_rate_limit_window_seconds: int = 900

    auth_otp_request_email_limit: int = 5
    auth_otp_request_ip_limit: int = 20

    auth_otp_verify_email_limit: int = 10
    auth_otp_verify_ip_limit: int = 30

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        # The file also contains Compose and Uvicorn configuration.
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
