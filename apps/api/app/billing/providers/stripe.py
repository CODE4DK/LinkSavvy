"""Stripe adapter -- Checkout + Billing Portal + webhook verification
against Stripe's plain REST API (no SDK dependency, mirroring how
app/ai/providers' vendor adapters call out over `httpx` directly).

Requires `settings.stripe_api_key` and `settings.stripe_webhook_secret`.
Neither is required for the app to boot; calling this adapter without
them raises `BillingProviderError` on first use, not at import time.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
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

_API_BASE = "https://api.stripe.com/v1"
_WEBHOOK_TOLERANCE_SECONDS = 300

_EVENT_TYPE_MAP: dict[str, NormalisedEventType] = {
    "customer.subscription.created": NormalisedEventType.SUBSCRIPTION_ACTIVATED,
    "invoice.paid": NormalisedEventType.SUBSCRIPTION_RENEWED,
    "invoice.payment_failed": NormalisedEventType.SUBSCRIPTION_PAYMENT_FAILED,
    "customer.subscription.deleted": NormalisedEventType.SUBSCRIPTION_CANCELLED,
    "customer.subscription.updated": NormalisedEventType.SUBSCRIPTION_PLAN_CHANGED,
    "charge.refunded": NormalisedEventType.REFUND_ISSUED,
}


class StripeProvider(BillingProvider):
    name = "stripe"

    def _require_api_key(self) -> str:
        if not settings.stripe_api_key:
            raise BillingProviderError("STRIPE_API_KEY is not configured")
        return settings.stripe_api_key

    async def _post(self, path: str, *, data: dict[str, Any]) -> dict[str, Any]:
        api_key = self._require_api_key()
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(f"{_API_BASE}{path}", data=data, auth=(api_key, ""))
            except httpx.HTTPError as exc:
                raise BillingProviderError(f"stripe request failed: {exc}") from exc
        if response.status_code >= 400:
            raise BillingProviderError(f"stripe error {response.status_code}: {response.text}")
        result: dict[str, Any] = response.json()
        return result

    async def create_checkout(self, *, user: User, plan: str, interval: str) -> CheckoutSession:
        price_id = settings.stripe_price_ids.get(f"{plan}:{interval}")
        if not price_id:
            raise BillingProviderError(f"no stripe price configured for {plan}:{interval}")
        data = {
            "mode": "subscription",
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "success_url": f"{settings.frontend_url}{settings.billing_checkout_success_path}",
            "cancel_url": f"{settings.frontend_url}{settings.billing_checkout_cancel_path}",
            "client_reference_id": str(user.id),
            "customer_email": user.email,
            "subscription_data[metadata][user_id]": str(user.id),
        }
        session = await self._post("/checkout/sessions", data=data)
        return CheckoutSession(url=session["url"], provider_session_id=session["id"])

    async def create_portal_session(self, *, customer_id: str) -> str:
        session = await self._post(
            "/billing_portal/sessions",
            data={
                "customer": customer_id,
                "return_url": settings.frontend_url + "/billing/manage",
            },
        )
        return str(session["url"])

    async def cancel(self, *, subscription: Subscription, at_period_end: bool) -> None:
        if not subscription.provider_subscription_id:
            raise BillingProviderError("subscription has no provider_subscription_id")
        if at_period_end:
            await self._post(
                f"/subscriptions/{subscription.provider_subscription_id}",
                data={"cancel_at_period_end": "true"},
            )
        else:
            api_key = self._require_api_key()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{_API_BASE}/subscriptions/{subscription.provider_subscription_id}",
                    auth=(api_key, ""),
                )
            if response.status_code >= 400:
                raise BillingProviderError(f"stripe cancel failed: {response.text}")

    async def delete_customer(self, *, customer_id: str) -> None:
        api_key = self._require_api_key()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(
                f"{_API_BASE}/customers/{customer_id}", auth=(api_key, "")
            )
        if response.status_code >= 400:
            raise BillingProviderError(f"stripe customer deletion failed: {response.text}")

    async def change_plan(self, *, subscription: Subscription, plan: str, interval: str) -> None:
        price_id = settings.stripe_price_ids.get(f"{plan}:{interval}")
        if not price_id:
            raise BillingProviderError(f"no stripe price configured for {plan}:{interval}")
        if not subscription.provider_subscription_id:
            raise BillingProviderError("subscription has no provider_subscription_id")
        await self._post(
            f"/subscriptions/{subscription.provider_subscription_id}",
            data={"items[0][price]": price_id, "proration_behavior": "create_prorations"},
        )

    def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> NormalisedEvent:
        if not settings.stripe_webhook_secret:
            raise BillingProviderError("STRIPE_WEBHOOK_SECRET is not configured")
        _verify_stripe_signature(
            headers.get("stripe-signature", ""), body, settings.stripe_webhook_secret
        )
        payload = json.loads(body)
        return self.parse_payload(payload)

    def parse_payload(self, payload: dict[str, Any]) -> NormalisedEvent:
        """The signature-verified half of `parse_webhook`, split out so
        admin webhook replay (app/admin/subscriptions.py) can re-run
        processing against a payload already persisted in `webhook_events`
        without needing (and being unable to reconstruct) a fresh
        signature."""
        stripe_type = payload["type"]
        event_type = _EVENT_TYPE_MAP.get(stripe_type)
        if event_type is None:
            raise BillingProviderError(f"unhandled stripe event type: {stripe_type}")

        obj = payload["data"]["object"]
        price_id = None
        items = (obj.get("items") or {}).get("data") or []
        if items:
            price_id = (items[0].get("price") or {}).get("id")
        plan, interval = _reverse_price_lookup(price_id)

        return NormalisedEvent(
            type=event_type,
            provider_event_id=payload["id"],
            provider_subscription_id=obj.get("subscription") or obj.get("id"),
            provider_customer_id=obj.get("customer"),
            status=obj.get("status"),
            plan=plan,
            interval=interval,
            current_period_start=_epoch(obj.get("current_period_start")),
            current_period_end=_epoch(obj.get("current_period_end")),
            cancel_at_period_end=obj.get("cancel_at_period_end"),
            currency=obj.get("currency"),
            amount_minor=obj.get("amount_paid") or obj.get("amount_due"),
            provider_payment_id=obj.get("payment_intent") or obj.get("id"),
            failure_reason=(obj.get("last_payment_error") or {}).get("message"),
            invoice_url=obj.get("hosted_invoice_url"),
            user_id_hint=(obj.get("metadata") or {}).get("user_id"),
            raw=payload,
        )


def _reverse_price_lookup(price_id: str | None) -> tuple[str | None, str | None]:
    """`settings.stripe_price_ids` maps "plan:interval" -> price id; a
    webhook only ever gives us the price id back, so this is the one
    place that runs the mapping backwards. Best-effort: an unrecognised
    price id (a price retired since the subscription started, say) simply
    yields (None, None), and the caller keeps whatever plan/interval it
    already had on file rather than guessing."""
    for key, configured_price_id in settings.stripe_price_ids.items():
        if configured_price_id == price_id:
            plan, interval = key.split(":", 1)
            return plan, interval
    return None, None


def _epoch(value: int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value, tz=UTC)


def _verify_stripe_signature(header: str, body: bytes, secret: str) -> None:
    """Stripe's documented scheme: `t=<ts>,v1=<hmac>[,v0=...]`, verified as
    `HMAC-SHA256(secret, f"{t}.{payload}")`, with a tolerance window to
    reject replayed-but-stale deliveries."""
    parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        raise BillingProviderError("malformed Stripe-Signature header")
    if abs(time.time() - int(timestamp)) > _WEBHOOK_TOLERANCE_SECONDS:
        raise BillingProviderError("Stripe webhook timestamp outside tolerance")
    signed_payload = f"{timestamp}.{body.decode('utf-8')}".encode()
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise BillingProviderError("Stripe webhook signature mismatch")
