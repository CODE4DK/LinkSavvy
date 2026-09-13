"""Razorpay adapter -- Subscriptions API + webhook verification, for
users whose billing country routes them here (India; see
app/billing/providers/registry.py).

Razorpay has no hosted "checkout session" the way Stripe does: creating a
subscription server-side returns a `short_url` that opens Razorpay's
Checkout overlay pre-bound to that subscription, which is what
`create_checkout` returns as its `url`. Razorpay also has no customer
portal API, so `create_portal_session` raises -- the manage-subscription
page falls back to in-app cancel/change-plan actions for Razorpay
subscribers instead of a hosted portal link (see docs/adr/0011).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx

from app.billing.providers.base import (
    BillingProvider,
    BillingProviderError,
    CheckoutSession,
    NormalisedEvent,
    NormalisedEventType,
)
from app.settings import settings

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.user import User

_API_BASE = "https://api.razorpay.com/v1"

_EVENT_TYPE_MAP: dict[str, NormalisedEventType] = {
    "subscription.activated": NormalisedEventType.SUBSCRIPTION_ACTIVATED,
    "subscription.charged": NormalisedEventType.SUBSCRIPTION_RENEWED,
    "subscription.pending": NormalisedEventType.SUBSCRIPTION_PAYMENT_FAILED,
    "subscription.cancelled": NormalisedEventType.SUBSCRIPTION_CANCELLED,
    "subscription.updated": NormalisedEventType.SUBSCRIPTION_PLAN_CHANGED,
    "refund.processed": NormalisedEventType.REFUND_ISSUED,
}


class RazorpayProvider(BillingProvider):
    name = "razorpay"

    def _require_keys(self) -> tuple[str, str]:
        if not settings.razorpay_key_id or not settings.razorpay_key_secret:
            raise BillingProviderError("Razorpay keys are not configured")
        return settings.razorpay_key_id, settings.razorpay_key_secret

    async def _post(self, path: str, *, data: dict[str, Any]) -> dict[str, Any]:
        key_id, key_secret = self._require_keys()
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{_API_BASE}{path}", json=data, auth=(key_id, key_secret)
                )
            except httpx.HTTPError as exc:
                raise BillingProviderError(f"razorpay request failed: {exc}") from exc
        if response.status_code >= 400:
            raise BillingProviderError(f"razorpay error {response.status_code}: {response.text}")
        result: dict[str, Any] = response.json()
        return result

    async def create_checkout(self, *, user: User, plan: str, interval: str) -> CheckoutSession:
        plan_id = settings.razorpay_plan_ids.get(f"{plan}:{interval}")
        if not plan_id:
            raise BillingProviderError(f"no razorpay plan configured for {plan}:{interval}")
        subscription = await self._post(
            "/subscriptions",
            data={
                "plan_id": plan_id,
                "total_count": 120 if interval == "month" else 10,
                "notes": {"user_id": str(user.id)},
                "notify_info": {"notify_email": user.email},
            },
        )
        return CheckoutSession(
            url=subscription["short_url"], provider_session_id=subscription["id"]
        )

    async def create_portal_session(self, *, customer_id: str) -> str:
        raise BillingProviderError(
            "Razorpay has no hosted billing portal; manage the subscription in-app"
        )

    async def cancel(self, *, subscription: Subscription, at_period_end: bool) -> None:
        if not subscription.provider_subscription_id:
            raise BillingProviderError("subscription has no provider_subscription_id")
        await self._post(
            f"/subscriptions/{subscription.provider_subscription_id}/cancel",
            data={"cancel_at_cycle_end": 1 if at_period_end else 0},
        )

    async def change_plan(self, *, subscription: Subscription, plan: str, interval: str) -> None:
        plan_id = settings.razorpay_plan_ids.get(f"{plan}:{interval}")
        if not plan_id:
            raise BillingProviderError(f"no razorpay plan configured for {plan}:{interval}")
        if not subscription.provider_subscription_id:
            raise BillingProviderError("subscription has no provider_subscription_id")
        await self._post(
            f"/subscriptions/{subscription.provider_subscription_id}",
            data={"plan_id": plan_id, "schedule_change_at": "cycle_end"},
        )

    def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> NormalisedEvent:
        if not settings.razorpay_webhook_secret:
            raise BillingProviderError("RAZORPAY_WEBHOOK_SECRET is not configured")
        _verify_razorpay_signature(
            headers.get("x-razorpay-signature", ""), body, settings.razorpay_webhook_secret
        )
        payload = json.loads(body)
        return self.parse_payload(payload)

    def parse_payload(self, payload: dict[str, Any]) -> NormalisedEvent:
        razorpay_type = payload["event"]
        event_type = _EVENT_TYPE_MAP.get(razorpay_type)
        if event_type is None:
            raise BillingProviderError(f"unhandled razorpay event type: {razorpay_type}")

        entity_key = "subscription" if "subscription" in payload["payload"] else "payment"
        entity = payload["payload"][entity_key]["entity"]
        payment_entity = payload["payload"].get("payment", {}).get("entity", {})
        plan, interval = _reverse_plan_lookup(entity.get("plan_id"))

        return NormalisedEvent(
            type=event_type,
            provider_event_id=payload["event"] + ":" + str(payload.get("created_at", entity["id"])),
            provider_subscription_id=entity.get("id") if entity_key == "subscription" else None,
            provider_customer_id=entity.get("customer_id") or payment_entity.get("customer_id"),
            status=entity.get("status"),
            plan=plan,
            interval=interval,
            current_period_start=_epoch(entity.get("current_start")),
            current_period_end=_epoch(entity.get("current_end")),
            cancel_at_period_end=bool(entity.get("cancel_at_cycle_end")),
            currency=payment_entity.get("currency"),
            amount_minor=payment_entity.get("amount"),
            provider_payment_id=payment_entity.get("id"),
            failure_reason=payment_entity.get("error_description"),
            invoice_url=None,
            user_id_hint=(entity.get("notes") or {}).get("user_id"),
            raw=payload,
        )


def _reverse_plan_lookup(plan_id: str | None) -> tuple[str | None, str | None]:
    for key, configured_plan_id in settings.razorpay_plan_ids.items():
        if configured_plan_id == plan_id:
            plan, interval = key.split(":", 1)
            return plan, interval
    return None, None


def _epoch(value: int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=UTC)


def _verify_razorpay_signature(signature: str, body: bytes, secret: str) -> None:
    """Razorpay's documented scheme: `HMAC-SHA256(secret, raw_body)` as a
    hex digest, compared to the `X-Razorpay-Signature` header."""
    if not signature:
        raise BillingProviderError("missing X-Razorpay-Signature header")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise BillingProviderError("Razorpay webhook signature mismatch")
