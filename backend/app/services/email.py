"""Transactional (verification/reset) email -- routed through the same
EMAIL_PROVIDER-selected sender as app/notifications/email/ (default
"console", so local dev needs no mail server at all; set EMAIL_PROVIDER=smtp
to route through a real SMTP catcher like MailHog instead)."""

from __future__ import annotations

from app.notifications.email.base import OutboundEmail
from app.notifications.email.registry import get_email_sender
from app.settings import settings


async def send_email(*, to: str, subject: str, text_body: str, html_body: str) -> None:
    sender = get_email_sender()
    await sender.send(
        OutboundEmail(to=to, subject=subject, text_body=text_body, html_body=html_body)
    )


async def send_verification_email(*, to: str, token: str) -> None:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    await send_email(
        to=to,
        subject="Verify your LinkSavvy email",
        text_body=f"Confirm your email address: {link}",
        html_body=f'<p>Confirm your email address:</p><p><a href="{link}">{link}</a></p>',
    )


async def send_password_reset_email(*, to: str, token: str) -> None:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    await send_email(
        to=to,
        subject="Reset your LinkSavvy password",
        text_body=f"Reset your password: {link}",
        html_body=f'<p>Reset your password:</p><p><a href="{link}">{link}</a></p>',
    )
