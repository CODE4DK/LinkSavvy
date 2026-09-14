from __future__ import annotations

from functools import lru_cache

from app.notifications.email.base import EmailSender
from app.notifications.email.console import ConsoleEmailSender
from app.notifications.email.resend import ResendEmailSender
from app.notifications.email.ses import SesEmailSender
from app.notifications.email.smtp import SmtpEmailSender
from app.settings import settings

_SENDER_CLASSES: dict[str, type[EmailSender]] = {
    "console": ConsoleEmailSender,
    "smtp": SmtpEmailSender,
    "resend": ResendEmailSender,
    "ses": SesEmailSender,
}


@lru_cache(maxsize=1)
def _build(provider_name: str) -> EmailSender:
    # Tests monkeypatch this dict itself (the same pattern as
    # app/ai/providers/registry.py and app/billing/providers/registry.py).
    return _SENDER_CLASSES[provider_name]()


def get_email_sender() -> EmailSender:
    return _build(settings.email_provider)
