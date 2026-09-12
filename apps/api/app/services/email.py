"""Transactional email, sent through MailHog in local dev."""

from __future__ import annotations

from email.message import EmailMessage

import aiosmtplib

from app.settings import settings


async def send_email(*, to: str, subject: str, text_body: str, html_body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
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
