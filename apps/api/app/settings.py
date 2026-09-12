"""Application settings.

Settings are read once from the environment at import time. Missing
required variables raise immediately (a `pydantic.ValidationError`) so a
misconfigured deployment fails at boot, not on the first request.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "test", "production"] = "development"

    # Required — no defaults. Missing any of these raises at import time.
    database_url: str
    jwt_secret: str
    refresh_token_pepper: str
    encryption_key: str

    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    email_verification_ttl_hours: int = 24
    password_reset_ttl_hours: int = 1

    frontend_url: str = "http://localhost:5173"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    mail_from: str = "LinkSavvy <no-reply@linksavvy.app>"

    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = None
    linkedin_redirect_uri: str | None = None
    # A second registered redirect URI for the profile-connect flow (Phase
    # 02), kept separate from sign-in's so the callback never has to guess
    # which flow it's completing.
    linkedin_profile_redirect_uri: str | None = None

    login_rate_limit_per_minute: int = 10
    register_rate_limit_per_minute: int = 5

    # How long raw pasted/uploaded profile input is retained (encrypted at
    # rest) before it's eligible for purge. The parsed ProfileSnapshot it
    # produced is kept indefinitely as a normal snapshot version; this only
    # governs the original text/file.
    profile_import_retention_days: int = 30
    profile_paste_max_bytes: int = 200_000
    profile_upload_max_bytes: int = 10_000_000


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
