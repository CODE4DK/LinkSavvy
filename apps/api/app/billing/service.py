"""The billing domain service: checkout, portal, cancel, plan change, and
--- the one source of truth for entitlements --- idempotent webhook
processing.

Never grants a plan change from a client-side redirect. `create_checkout`
only ever returns a URL to the provider's hosted page; the *only* function
that ever calls `apply_entitlements` is `process_webhook_event`. The
frontend's post-checkout screen polls `GET /billing/subscription` until
the webhook has landed rather than assuming success from the redirect
itself (see docs/adr/0011).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.entitlements import apply_entitlements
from app.billing.providers.base import (
    BillingProvider,
    BillingProviderError,
    CheckoutSession,
    NormalisedEvent,
    NormalisedEventType,
)
from app.billing.providers.registry import get_provider, provider_name_for_billing_country
from app.errors import ApiError, ErrorCode
from app.jobs.queue import enqueue
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.models.webhook_event import WebhookEvent

_NOTIFICATION_JOB_TYPE = "notifications.dispatch"


class NoActiveSubscription(ApiError):
    def __init__(self) -> None:
        super().__init__(ErrorCode.NO_ACTIVE_SUBSCRIPTION, "This account has no subscription yet")


async def get_or_create_subscription(db: AsyncSession, *, user: User) -> Subscription:
    subscription = (
        await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    ).scalar_one_or_none()
    if subscription is not None:
        return subscription

    provider_name = provider_name_for_billing_country(user.billing_country)
    subscription = Subscription(user_id=user.id, provider=provider_name, plan="free")
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def create_checkout_session(
    db: AsyncSession, *, user: User, plan: str, interval: str
) -> CheckoutSession:
    subscription = await get_or_create_subscription(db, user=user)
    provider = get_provider(subscription.provider)
    try:
        return await provider.create_checkout(user=user, plan=plan, interval=interval)
    except BillingProviderError as exc:
        raise ApiError(ErrorCode.BILLING_PROVIDER_ERROR, str(exc)) from exc


async def create_portal_session(db: AsyncSession, *, user: User) -> str:
    subscription = await get_or_create_subscription(db, user=user)
    if not subscription.provider_customer_id:
        raise NoActiveSubscription()
    provider = get_provider(subscription.provider)
    try:
        return await provider.create_portal_session(customer_id=subscription.provider_customer_id)
    except BillingProviderError as exc:
        raise ApiError(ErrorCode.BILLING_PROVIDER_ERROR, str(exc)) from exc


async def cancel_subscription(
    db: AsyncSession, *, user: User, at_period_end: bool = True
) -> Subscription:
    subscription = await get_or_create_subscription(db, user=user)
    if not subscription.provider_subscription_id:
        raise NoActiveSubscription()
    provider = get_provider(subscription.provider)
    try:
        await provider.cancel(subscription=subscription, at_period_end=at_period_end)
    except BillingProviderError as exc:
        raise ApiError(ErrorCode.BILLING_PROVIDER_ERROR, str(exc)) from exc

    # Optimistic local update -- the webhook is still what confirms this,
    # but reflecting the request immediately is what lets the UI show
    # "cancels on <date>" without waiting a round trip.
    subscription.cancel_at_period_end = at_period_end
    if not at_period_end:
        subscription.status = "cancelled"
    await db.commit()
    await db.refresh(subscription)
    return subscription


async def change_plan(db: AsyncSession, *, user: User, plan: str, interval: str) -> Subscription:
    subscription = await get_or_create_subscription(db, user=user)
    if not subscription.provider_subscription_id:
        raise NoActiveSubscription()
    provider = get_provider(subscription.provider)
    try:
        await provider.change_plan(subscription=subscription, plan=plan, interval=interval)
    except BillingProviderError as exc:
        raise ApiError(ErrorCode.BILLING_PROVIDER_ERROR, str(exc)) from exc
    return subscription


async def _find_subscription_for_event(
    db: AsyncSession, *, provider_name: str, event: NormalisedEvent
) -> Subscription | None:
    if event.provider_subscription_id:
        existing = (
            await db.execute(
                select(Subscription).where(
                    Subscription.provider == provider_name,
                    Subscription.provider_subscription_id == event.provider_subscription_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    if event.user_id_hint:
        by_user = (
            await db.execute(
                select(Subscription).where(
                    Subscription.user_id == uuid.UUID(event.user_id_hint),
                    Subscription.provider == provider_name,
                )
            )
        ).scalar_one_or_none()
        if by_user is not None:
            return by_user

    if event.provider_payment_id:
        payment = (
            await db.execute(
                select(Payment).where(Payment.provider_payment_id == event.provider_payment_id)
            )
        ).scalar_one_or_none()
        if payment is not None:
            return await db.get(Subscription, payment.subscription_id)

    return None


def _is_newer_or_equal(incoming_end: datetime | None, current_end: datetime | None) -> bool:
    """Guards against processing an out-of-order webhook delivery: a
    period-end timestamp that is *older* than what's already stored means
    this event arrived late (providers make no ordering guarantee), and
    applying it would roll the subscription's clock backwards."""
    if incoming_end is None:
        return True
    if current_end is None:
        return True
    return incoming_end >= current_end


async def _notify(
    db: AsyncSession, *, user_id: uuid.UUID, notif_type: str, title: str, body: str, route: str
) -> None:
    # Decoupled from app.notifications on purpose: this module is written
    # before that one exists in the phase's commit sequence, and jobs
    # queued for a type with no handler registered yet simply sit queued
    # (harmlessly) until the notifications section registers one -- see
    # app/notifications/dispatch_job.py.
    await enqueue(
        db,
        job_type=_NOTIFICATION_JOB_TYPE,
        payload={"type": notif_type, "title": title, "body": body, "action_route": route},
        user_id=user_id,
    )


async def process_webhook_event(
    db: AsyncSession, *, provider_name: str, headers: dict[str, str], body: bytes
) -> WebhookEvent:
    provider: BillingProvider = get_provider(provider_name)
    try:
        event = provider.parse_webhook(headers=headers, body=body)
    except BillingProviderError as exc:
        raise ApiError(ErrorCode.WEBHOOK_SIGNATURE_INVALID, str(exc)) from exc

    now = datetime.now(UTC)

    # Persist first, keyed on the provider's own event id, so a retried
    # delivery (every provider retries until it sees a 2xx) is a no-op
    # rather than a double-apply. The unique constraint is the actual
    # guarantee; the SELECT-first path just avoids paying for a doomed
    # INSERT on the common case (a genuine replay).
    existing = (
        await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.provider == provider_name,
                WebhookEvent.provider_event_id == event.provider_event_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.status == "processed":
            return existing
        record = existing
        record.attempts += 1
    else:
        record = WebhookEvent(
            provider=provider_name,
            provider_event_id=event.provider_event_id,
            type=event.type.value,
            payload=event.raw,
            received_at=now,
            status="pending",
            attempts=1,
        )
        db.add(record)
        try:
            await db.flush()
        except IntegrityError:
            # Lost a race with a concurrent delivery of the same event;
            # the other request is processing it, so this one is done.
            await db.rollback()
            winner = (
                await db.execute(
                    select(WebhookEvent).where(
                        WebhookEvent.provider == provider_name,
                        WebhookEvent.provider_event_id == event.provider_event_id,
                    )
                )
            ).scalar_one()
            return winner

    try:
        await _apply_normalised_event(db, provider_name=provider_name, event=event)
    except Exception as exc:  # noqa: BLE001 -- recorded on the row, then re-raised
        record.status = "failed"
        record.error = str(exc)
        await db.commit()
        raise

    record.status = "processed"
    record.processed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(record)
    return record


async def reprocess_stored_event(db: AsyncSession, *, webhook_event_id: uuid.UUID) -> WebhookEvent:
    """Admin-triggered replay (app/admin/subscriptions.py): re-runs
    processing against a payload already sitting in `webhook_events`,
    using `parse_payload` (no signature check -- there's nothing left to
    verify against our own stored copy). Intended for an event whose
    first attempt failed outright; replaying an event that already fully
    succeeded can duplicate a side effect like a `Payment` row, the same
    caveat a real provider's own "resend webhook" tooling carries."""
    record = await db.get(WebhookEvent, webhook_event_id)
    if record is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such webhook event")

    provider = get_provider(record.provider)
    event = provider.parse_payload(record.payload)
    record.attempts += 1

    try:
        await _apply_normalised_event(db, provider_name=record.provider, event=event)
    except Exception as exc:  # noqa: BLE001 -- recorded on the row, then re-raised
        record.status = "failed"
        record.error = str(exc)
        await db.commit()
        raise

    record.status = "processed"
    record.processed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(record)
    return record


async def _apply_normalised_event(
    db: AsyncSession, *, provider_name: str, event: NormalisedEvent
) -> None:
    subscription = await _find_subscription_for_event(db, provider_name=provider_name, event=event)

    if subscription is None:
        if event.user_id_hint is None:
            # Nothing to correlate this to (e.g. a refund on a payment we
            # have no record of) -- log-worthy, not fatal.
            return
        subscription = Subscription(
            user_id=uuid.UUID(event.user_id_hint), provider=provider_name, plan="free"
        )
        db.add(subscription)
        await db.flush()

    if event.provider_subscription_id:
        subscription.provider_subscription_id = event.provider_subscription_id
    if event.provider_customer_id:
        subscription.provider_customer_id = event.provider_customer_id

    user = await db.get(User, subscription.user_id)
    assert user is not None

    if event.type == NormalisedEventType.SUBSCRIPTION_ACTIVATED:
        subscription.status = event.status or "active"
        subscription.plan = event.plan or subscription.plan or "pro"
        if event.interval:
            subscription.interval = event.interval
        if _is_newer_or_equal(event.current_period_end, subscription.current_period_end):
            subscription.current_period_start = event.current_period_start
            subscription.current_period_end = event.current_period_end
        if event.trial_ends_at:
            subscription.trial_ends_at = event.trial_ends_at
        if event.currency:
            subscription.currency = event.currency
        if event.amount_minor is not None:
            subscription.amount_minor = event.amount_minor
        await apply_entitlements(db, user=user, plan="pro")
        await _notify(
            db,
            user_id=user.id,
            notif_type="subscription.activated",
            title="Welcome to LinkSavvy Pro",
            body="Your subscription is active. All pro tools and limits are unlocked.",
            route="/billing/manage",
        )

    elif event.type == NormalisedEventType.SUBSCRIPTION_RENEWED:
        if _is_newer_or_equal(event.current_period_end, subscription.current_period_end):
            subscription.current_period_start = event.current_period_start
            subscription.current_period_end = event.current_period_end
        subscription.status = "active"
        if event.provider_payment_id:
            db.add(
                Payment(
                    subscription_id=subscription.id,
                    provider_payment_id=event.provider_payment_id,
                    amount_minor=event.amount_minor or 0,
                    currency=event.currency or subscription.currency,
                    status="succeeded",
                    invoice_url=event.invoice_url,
                    paid_at=datetime.now(UTC),
                )
            )
        await apply_entitlements(db, user=user, plan="pro")

    elif event.type == NormalisedEventType.SUBSCRIPTION_PAYMENT_FAILED:
        # Only escalate forward -- a late-arriving failure for a period
        # the account has already recovered from (or cancelled out of)
        # must not roll status back to past_due.
        if subscription.status in ("trialing", "active"):
            subscription.status = "past_due"
        if event.provider_payment_id:
            db.add(
                Payment(
                    subscription_id=subscription.id,
                    provider_payment_id=event.provider_payment_id,
                    amount_minor=event.amount_minor or 0,
                    currency=event.currency or subscription.currency,
                    status="failed",
                    failure_reason=event.failure_reason,
                )
            )
        await _notify(
            db,
            user_id=user.id,
            notif_type="billing.payment_failed",
            title="We couldn't process your payment",
            body=(
                "Your last payment failed. You'll keep full access for "
                f"{_grace_period_days()} days while we retry -- update your "
                "payment method to avoid any interruption."
            ),
            route="/billing/manage",
        )

    elif event.type == NormalisedEventType.SUBSCRIPTION_CANCELLED:
        subscription.status = "cancelled"
        subscription.cancel_at_period_end = False
        # Access continues until current_period_end -- see
        # app/billing/period_sweep.py, which is what actually flips the
        # plan back to free once that date passes.
        await _notify(
            db,
            user_id=user.id,
            notif_type="subscription.cancelled",
            title="Your subscription has been cancelled",
            body="You'll keep pro access until the end of your current billing period.",
            route="/billing/manage",
        )

    elif event.type == NormalisedEventType.SUBSCRIPTION_PLAN_CHANGED:
        if event.plan:
            subscription.plan = event.plan
        if event.interval:
            subscription.interval = event.interval
        if event.status:
            subscription.status = event.status
        if _is_newer_or_equal(event.current_period_end, subscription.current_period_end):
            subscription.current_period_start = event.current_period_start
            subscription.current_period_end = event.current_period_end
        await apply_entitlements(db, user=user, plan=subscription.plan)
        await _notify(
            db,
            user_id=user.id,
            notif_type="subscription.plan_changed",
            title="Your plan has changed",
            body=f"Your subscription is now on the {subscription.plan} plan.",
            route="/billing/manage",
        )

    elif event.type == NormalisedEventType.REFUND_ISSUED:
        if event.provider_payment_id:
            payment = (
                await db.execute(
                    select(Payment).where(Payment.provider_payment_id == event.provider_payment_id)
                )
            ).scalar_one_or_none()
            if payment is not None:
                payment.status = "refunded"

    await db.flush()


def _grace_period_days() -> int:
    from app.settings import settings

    return settings.past_due_grace_period_days
