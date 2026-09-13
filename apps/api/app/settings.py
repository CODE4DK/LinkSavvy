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

    # AI Gateway (Phase 03). No model string lives here or anywhere else —
    # see config/models.yaml and app/ai/providers/registry.py. Both keys
    # are optional so the app still boots without them; a provider raises
    # a clear, non-retryable ProviderError the first time it's actually
    # called without its key configured.
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    ai_cache_default_ttl_seconds: int = 3600

    # Billing (Phase 10). Optional so the app still boots without them; a
    # provider adapter raises BILLING_PROVIDER_ERROR the first time it's
    # actually called without its keys configured. Region routing (see
    # app/billing/providers/registry.py) picks Stripe or Razorpay per
    # user; both sets of keys are only needed once you actually sell into
    # both regions.
    stripe_api_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_ids: dict[str, str] = Field(default_factory=dict)  # "pro:month" -> price id
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    razorpay_plan_ids: dict[str, str] = Field(default_factory=dict)
    billing_checkout_success_path: str = "/billing/checkout-return?status=success"
    billing_checkout_cancel_path: str = "/billing/checkout-return?status=cancelled"
    # India billing country routes to Razorpay; everyone else to Stripe.
    razorpay_billing_countries: frozenset[str] = frozenset({"IN"})
    # How many days a `past_due` subscription keeps full access before
    # entitlements are restricted to the free plan (see
    # app/billing/entitlements.py::apply_entitlements).
    past_due_grace_period_days: int = 7

    # Notifications (Phase 10).
    email_provider: Literal["console", "resend", "ses"] = "console"
    resend_api_key: str | None = None
    ses_region: str | None = None
    unsubscribe_secret: str = "dev-unsubscribe-secret-change-in-production"

    # Privacy (Phase 10). How long a soft-deleted account's PII is kept
    # before the scheduled purge job hard-deletes it -- see
    # app/privacy/purge_scheduler.py and docs/privacy.md.
    account_hard_delete_after_days: int = 30
    ai_invocation_payload_retention_days: int = 90
    log_retention_days: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
