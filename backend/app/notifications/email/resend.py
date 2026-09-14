"""Resend's HTTP API -- a plain `httpx` call, the same style as the
Stripe/Razorpay adapters in app/billing/providers/*.py (no vendor SDK
dependency for one JSON POST)."""

from __future__ import annotations

import httpx

from app.notifications.email.base import EmailSender, EmailSendError, OutboundEmail
from app.settings import settings

_API_URL = "https://api.resend.com/emails"


class ResendEmailSender(EmailSender):
    async def send(self, message: OutboundEmail) -> str:
        if not settings.resend_api_key:
            raise EmailSendError("RESEND_API_KEY is not configured")

        headers = {"Authorization": f"Bearer {settings.resend_api_key}"}
        payload: dict[str, object] = {
            "from": settings.mail_from,
            "to": [message.to],
            "subject": message.subject,
            "html": message.html_body,
            "text": message.text_body,
        }
        if message.unsubscribe_url:
            payload["headers"] = {
                "List-Unsubscribe": f"<{message.unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(_API_URL, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                raise EmailSendError(f"resend request failed: {exc}") from exc
        if response.status_code >= 400:
            raise EmailSendError(f"resend error {response.status_code}: {response.text}")
        return str(response.json()["id"])
