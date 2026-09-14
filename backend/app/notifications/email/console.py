"""Logs the email instead of sending it -- the default so the test suite
and a first local run never need any mail infrastructure configured."""

from __future__ import annotations

import logging
import uuid

from app.notifications.email.base import EmailSender, OutboundEmail

logger = logging.getLogger("app.notifications.email.console")


class ConsoleEmailSender(EmailSender):
    async def send(self, message: OutboundEmail) -> str:
        message_id = f"console-{uuid.uuid4().hex[:12]}"
        logger.info(
            "email_would_send",
            extra={
                "to": message.to,
                "subject": message.subject,
                "message_id": message_id,
                "has_unsubscribe": message.unsubscribe_url is not None,
            },
        )
        return message_id
