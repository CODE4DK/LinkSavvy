"""Billing HTTP surface: pricing (read-only, driven by plan_limits),
checkout/portal/cancel/change-plan, and the two webhook endpoints. The
webhook endpoints are the only ones in this router that don't take
`get_current_user` -- they're authenticated by provider signature
instead (see app/billing/providers/*.py's `parse_webhook`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing import service as billing_service
from app.billing.plan_limits_seed import DEFAULT_PLAN_LIMITS
from app.deps import get_current_user, get_db
from app.models.payment import Payment
from app.models.plan_limit import PlanLimit
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.billing import (
    CancelSubscriptionRequest,
    ChangePlanRequest,
    CheckoutRequest,
    CheckoutResponse,
    PaymentResponse,
    PlanLimitResponse,
    PortalResponse,
    PricingResponse,
    SubscriptionResponse,
)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


def _to_subscription_response(subscription: Subscription) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=str(subscription.id),
        provider=subscription.provider,
        plan=subscription.plan,  # type: ignore[arg-type]
        interval=subscription.interval,  # type: ignore[arg-type]
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        trial_ends_at=subscription.trial_ends_at,
        currency=subscription.currency,
        amount_minor=subscription.amount_minor,
    )


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing(db: AsyncSession = Depends(get_db)) -> PricingResponse:
    rows = (await db.execute(select(PlanLimit))).scalars().all()
    if not rows:
        # A brand-new / test database that hasn't seeded plan_limits yet
        # (see tests/conftest.py, migration 0003) -- fall back to the
        # same canonical defaults rather than showing an empty page.
        return PricingResponse(
            limits=[PlanLimitResponse.model_validate(row) for row in DEFAULT_PLAN_LIMITS],
            currency="usd",
        )
    return PricingResponse(
        limits=[
            PlanLimitResponse(
                plan=row.plan,  # type: ignore[arg-type]
                metric=row.metric,
                limit_value=row.limit_value,
                window=row.window,
                overage_behaviour=row.overage_behaviour,
            )
            for row in rows
        ],
        currency="usd",
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SubscriptionResponse:
    subscription = await billing_service.get_or_create_subscription(db, user=user)
    return _to_subscription_response(subscription)


@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[PaymentResponse]:
    subscription = await billing_service.get_or_create_subscription(db, user=user)
    rows = (
        (
            await db.execute(
                select(Payment)
                .where(Payment.subscription_id == subscription.id)
                .order_by(Payment.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        PaymentResponse(
            id=str(row.id),
            amount_minor=row.amount_minor,
            currency=row.currency,
            status=row.status,
            failure_reason=row.failure_reason,
            invoice_url=row.invoice_url,
            paid_at=row.paid_at,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    session = await billing_service.create_checkout_session(
        db, user=user, plan=payload.plan, interval=payload.interval
    )
    return CheckoutResponse(checkout_url=session.url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> PortalResponse:
    url = await billing_service.create_portal_session(db, user=user)
    return PortalResponse(portal_url=url)


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    payload: CancelSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    subscription = await billing_service.cancel_subscription(
        db, user=user, at_period_end=payload.at_period_end
    )
    return _to_subscription_response(subscription)


@router.post("/change-plan", response_model=SubscriptionResponse)
async def change_plan(
    payload: ChangePlanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    subscription = await billing_service.change_plan(
        db, user=user, plan=payload.plan, interval=payload.interval
    )
    return _to_subscription_response(subscription)


@router.post("/webhooks/stripe", status_code=200)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    body = await request.body()
    record = await billing_service.process_webhook_event(
        db, provider_name="stripe", headers=dict(request.headers), body=body
    )
    return {"status": record.status}


@router.post("/webhooks/razorpay", status_code=200)
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    body = await request.body()
    record = await billing_service.process_webhook_event(
        db, provider_name="razorpay", headers=dict(request.headers), body=body
    )
    return {"status": record.status}
