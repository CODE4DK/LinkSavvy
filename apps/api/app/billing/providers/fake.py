"""A deterministic, no-network billing provider for tests -- the billing
equivalent of app/ai/providers/fake_provider.py. Swapped in by
tests/conftest.py's fixture (see app/billing/providers/registry.py's
`_PROVIDER_CLASSES`), never reachable in production since region routing
only ever names "stripe" or "razorpay"."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.billing.providers.base import (
    BillingProvider,
    BillingProviderError,
    CheckoutSession,
    NormalisedEvent,
)

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.user import User

#: Test code pushes events here, then calls FakeProvider.parse_webhook
#: with a header containing the queued event's id to retrieve it --
#: avoids reimplementing real signature schemes just to exercise the
#: webhook endpoint end to end.
_QUEUED_EVENTS: dict[str, NormalisedEvent] = {}


def queue_event(event: NormalisedEvent) -> None:
    _QUEUED_EVENTS[event.provider_event_id] = event


def clear_queue() -> None:
    _QUEUED_EVENTS.clear()


class FakeProvider(BillingProvider):
    name = "fake"

    async def create_checkout(self, *, user: User, plan: str, interval: str) -> CheckoutSession:
        session_id = f"fake_cs_{uuid.uuid4().hex[:12]}"
        return CheckoutSession(
            url=f"https://fake-checkout.test/{session_id}", provider_session_id=session_id
        )

    async def create_portal_session(self, *, customer_id: str) -> str:
        return f"https://fake-portal.test/{customer_id}"

    async def cancel(self, *, subscription: Subscription, at_period_end: bool) -> None:
        return None

    async def change_plan(self, *, subscription: Subscription, plan: str, interval: str) -> None:
        return None

    def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> NormalisedEvent:
        # The fake's "signature" is simply naming a previously-queued
        # event by id -- a missing or unrecognised id is treated exactly
        # like a real provider's signature check failing, so router tests
        # can exercise the WEBHOOK_SIGNATURE_INVALID path without
        # reimplementing a real HMAC scheme.
        event_id = headers.get("x-fake-event-id")
        if not event_id or event_id not in _QUEUED_EVENTS:
            raise BillingProviderError("no queued fake event matches x-fake-event-id")
        return _QUEUED_EVENTS[event_id]

    def parse_payload(self, payload: dict[str, object]) -> NormalisedEvent:
        event_id = str(payload.get("provider_event_id", ""))
        if event_id not in _QUEUED_EVENTS:
            raise BillingProviderError("no queued fake event matches provider_event_id")
        return _QUEUED_EVENTS[event_id]
