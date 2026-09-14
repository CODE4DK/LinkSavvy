"""The one interface every email-sending backend must satisfy -- mirrors
app/ai/providers/base.py and app/billing/providers/base.py's own
one-interface-per-vendor shape for the same reason: nothing outside this
package knows which provider is actually configured.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OutboundEmail:
    to: str
    subject: str
    html_body: str
    text_body: str
    # RFC 8058 one-click unsubscribe -- both forms so every mail client
    # that honours List-Unsubscribe at all can act on it. None for
    # transactional email that has no per-type preference to turn off.
    unsubscribe_url: str | None = None


class EmailSendError(Exception):
    """A send failed in a way the caller can't recover from itself."""


class EmailSender(ABC):
    @abstractmethod
    async def send(self, message: OutboundEmail) -> str:
        """Returns a provider message id (or a locally-generated one for
        adapters with no such concept, like the console adapter)."""
