"""Reuses the same MailHog-backed SMTP sender Phase 01 built for
verification/reset email (app/services/email.py), so local dev sees
notification emails in the same place without a second mail server."""

from __future__ import annotations

import uuid
from email.message import EmailMessage as _StdEmailMessage

import aiosmtplib

from app.notifications.email.base import EmailSender, OutboundEmail
from app.settings import settings


class SmtpEmailSender(EmailSender):
    async def send(self, message: OutboundEmail) -> str:
        email = _StdEmailMessage()
        email["From"] = settings.mail_from
        email["To"] = message.to
        email["Subject"] = message.subject
        if message.unsubscribe_url:
            email["List-Unsubscribe"] = (
                f"<{message.unsubscribe_url}>, <mailto:{_unsubscribe_mailto()}>"
            )
            email["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
        email.set_content(message.text_body)
        email.add_alternative(message.html_body, subtype="html")

        await aiosmtplib.send(email, hostname=settings.smtp_host, port=settings.smtp_port)
        return f"smtp-{uuid.uuid4().hex[:12]}"


def _unsubscribe_mailto() -> str:
    return settings.mail_from.split("<")[-1].rstrip(">")
