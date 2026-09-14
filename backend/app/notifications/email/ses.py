"""AWS SES adapter. Deliberately narrower than the other adapters: SES
needs SigV4-signed requests, which means either the `boto3`/`aiobotocore`
dependency or hand-rolled request signing -- neither is justified until
LinkSavvy actually has an SES-based deployment target. `settings.email_provider`
can still be set to "ses" (the app boots fine either way), but calling this
adapter raises until it's genuinely implemented -- see docs/adr/0011 for
the reasoning, and app/notifications/email/resend.py for the fully
implemented alternative production provider.
"""

from __future__ import annotations

from app.notifications.email.base import EmailSender, EmailSendError, OutboundEmail


class SesEmailSender(EmailSender):
    async def send(self, message: OutboundEmail) -> str:
        raise EmailSendError(
            "SES support is not yet implemented -- set EMAIL_PROVIDER=resend, "
            "or implement SigV4 signing here before using EMAIL_PROVIDER=ses"
        )
