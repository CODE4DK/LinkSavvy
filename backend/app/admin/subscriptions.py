"""Admin view onto billing: list/filter subscriptions, see the webhook
history behind one, and replay a failed delivery."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.service import reprocess_stored_event
from app.errors import ApiError, ErrorCode
from app.models.subscription import Subscription
from app.models.webhook_event import WebhookEvent
from app.services.audit import record_audit_event

_PAGE_SIZE_DEFAULT = 25


@dataclass(frozen=True, slots=True)
class SubscriptionPage:
    items: list[Subscription]


async def list_subscriptions(
    db: AsyncSession, *, status: str | None = None, limit: int = _PAGE_SIZE_DEFAULT
) -> SubscriptionPage:
    query = select(Subscription)
    if status:
        query = query.where(Subscription.status == status)
    query = query.order_by(Subscription.updated_at.desc()).limit(limit)
    items = (await db.execute(query)).scalars().all()
    return SubscriptionPage(items=list(items))


async def get_webhook_history(
    db: AsyncSession, *, subscription_id: uuid.UUID, limit: int = 50
) -> list[WebhookEvent]:
    subscription = await db.get(Subscription, subscription_id)
    if subscription is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such subscription")

    query = select(WebhookEvent).where(WebhookEvent.provider == subscription.provider)
    events = (
        (await db.execute(query.order_by(WebhookEvent.received_at.desc()).limit(200)))
        .scalars()
        .all()
    )

    if not subscription.provider_subscription_id:
        return list(events)[:limit]

    # webhook_events has no subscription_id column (a webhook can arrive
    # before any subscription row exists to link it to -- see
    # app/billing/service.py::_apply_normalised_event) -- so history for
    # one subscription is found by scanning its provider's recent events
    # for the matching provider_subscription_id inside the stored payload,
    # rather than a join that would require every payload shape to expose
    # the id at the same JSON path.
    matching = [
        event
        for event in events
        if _payload_mentions_subscription(event.payload, subscription.provider_subscription_id)
    ]
    return matching[:limit]


def _payload_mentions_subscription(payload: dict[str, Any], provider_subscription_id: str) -> bool:
    return provider_subscription_id in json.dumps(payload)


async def replay_webhook(
    db: AsyncSession, *, admin_id: uuid.UUID, webhook_event_id: uuid.UUID
) -> WebhookEvent:
    record = await reprocess_stored_event(db, webhook_event_id=webhook_event_id)
    await record_audit_event(
        db,
        actor_user_id=admin_id,
        action="admin.webhook.replay",
        target_type="webhook_event",
        target_id=str(webhook_event_id),
    )
    await db.commit()
    return record
