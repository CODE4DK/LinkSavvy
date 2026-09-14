"""The one interface every payment provider integration must satisfy.

Nothing outside `app/billing/providers/` may reference a Stripe or
Razorpay SDK type, header name, or webhook payload shape — every other
module (the billing service, the router, admin tooling) speaks only in
`CheckoutSession` and `NormalisedEvent`. That mirrors app/ai/providers'
own abstraction (see its base.py) for exactly the same reason: swapping a
vendor, or adding a new one, never touches a caller.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.user import User


class NormalisedEventType(StrEnum):
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_PAYMENT_FAILED = "subscription.payment_failed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_PLAN_CHANGED = "subscription.plan_changed"
    REFUND_ISSUED = "refund.issued"


@dataclass(frozen=True, slots=True)
class CheckoutSession:
    url: str
    provider_session_id: str


@dataclass(frozen=True, slots=True)
class NormalisedEvent:
    """What every provider's `parse_webhook` reduces its payload to.

    Every field below is what the six event types above can actually
    carry; a given event only populates the ones relevant to it (a
    `refund.issued` has no `plan`, for instance). `raw` is kept for
    admin-panel drill-down and for fields a specific handler might need
    that the normalised set doesn't carry.
    """

    type: NormalisedEventType
    provider_event_id: str
    provider_subscription_id: str | None = None
    provider_customer_id: str | None = None
    status: str | None = None
    plan: str | None = None
    interval: str | None = None
    current_period_start: Any = None
    current_period_end: Any = None
    cancel_at_period_end: bool | None = None
    trial_ends_at: Any = None
    currency: str | None = None
    amount_minor: int | None = None
    provider_payment_id: str | None = None
    failure_reason: str | None = None
    invoice_url: str | None = None
    # Best-effort correlation hint for the very first event on a
    # subscription, before app/billing/service.py has anything else to
    # join on (see create_checkout on both adapters, which stash the
    # user id in provider-side metadata/notes for exactly this).
    user_id_hint: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class BillingProviderError(Exception):
    """A provider call failed in a way the caller can't recover from
    itself (bad credentials, the vendor API down, a malformed response).
    The router wraps this as ErrorCode.BILLING_PROVIDER_ERROR."""


class BillingProvider(ABC):
    name: str

    @abstractmethod
    async def create_checkout(self, *, user: User, plan: str, interval: str) -> CheckoutSession: ...

    @abstractmethod
    async def create_portal_session(self, *, customer_id: str) -> str:
        """Returns a URL to the provider's hosted billing-management
        portal (invoices, payment method) for this provider-side customer."""

    @abstractmethod
    async def cancel(self, *, subscription: Subscription, at_period_end: bool) -> None: ...

    @abstractmethod
    async def change_plan(
        self, *, subscription: Subscription, plan: str, interval: str
    ) -> None: ...

    @abstractmethod
    def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> NormalisedEvent:
        """Verifies the payload's signature (raising `BillingProviderError`
        if it doesn't check out) and reduces it to a `NormalisedEvent`."""

    @abstractmethod
    async def delete_customer(self, *, customer_id: str) -> None:
        """Removes the provider-side customer record -- part of a real
        account deletion (app/privacy/purge.py), not just our own DB row.
        A no-op (with a clear reason) is a valid implementation for a
        provider whose API has nothing equivalent to delete."""

    @abstractmethod
    def parse_payload(self, payload: dict[str, Any]) -> NormalisedEvent:
        """The signature-verified half of `parse_webhook`: turns an
        already-decoded payload into a `NormalisedEvent` with no signature
        check at all. Exists so admin webhook replay
        (app/admin/subscriptions.py) can re-run processing against a
        payload already persisted in `webhook_events` -- there is no
        signature left to re-verify by the time it's sitting in our own
        database, and re-deriving one is neither possible nor the point."""
