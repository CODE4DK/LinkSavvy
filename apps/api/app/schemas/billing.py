from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PlanLiteral = Literal["free", "pro"]
IntervalLiteral = Literal["month", "year"]


class CheckoutRequest(BaseModel):
    plan: PlanLiteral
    interval: IntervalLiteral = "month"


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class SubscriptionResponse(BaseModel):
    id: str
    provider: str
    plan: PlanLiteral
    interval: IntervalLiteral
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    trial_ends_at: datetime | None
    currency: str
    amount_minor: int


class CancelSubscriptionRequest(BaseModel):
    at_period_end: bool = True
    reason: str | None = Field(default=None, max_length=2000)


class ChangePlanRequest(BaseModel):
    plan: PlanLiteral
    interval: IntervalLiteral = "month"


class PaymentResponse(BaseModel):
    id: str
    amount_minor: int
    currency: str
    status: str
    failure_reason: str | None
    invoice_url: str | None
    paid_at: datetime | None
    created_at: datetime


class PlanLimitResponse(BaseModel):
    plan: PlanLiteral
    metric: str
    limit_value: int
    window: str
    overage_behaviour: str


class PricingResponse(BaseModel):
    """Built straight from `plan_limits` (see app/routers/billing.py) so
    the pricing page can never drift from what the app actually enforces."""

    limits: list[PlanLimitResponse]
    currency: str
