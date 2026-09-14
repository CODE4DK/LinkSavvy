"""Where the data-retention policy in docs/privacy.md actually gets
enforced: hard-deleting an account past its grace window, and sweeping
transient content (expired profile-import blobs, expired AI response
cache, old email-send logs) past its own retention period.

`audit_log` is deliberately never purged here -- it is the compliance
record of who did what, not user content, and its own `actor_user_id`
already goes to NULL (ondelete="SET NULL") the moment the actor is
hard-deleted, so it never outlives an account as identifying data.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.providers.base import BillingProviderError
from app.billing.providers.registry import get_provider
from app.errors import ApiError, ErrorCode
from app.models.ai_cache import AICache
from app.models.ai_invocation import AIInvocation
from app.models.base import Base
from app.models.data_export import DataExport
from app.models.email_log import EmailLog
from app.models.profile_import import ProfileImportBlob
from app.models.subscription import Subscription
from app.models.user import User
from app.settings import settings

logger = logging.getLogger("app.privacy.purge")


async def hard_delete_user(db: AsyncSession, *, user_id: uuid.UUID) -> None:
    """Real deletion, not another soft-delete pass. Walks every mapped
    table with a direct `user_id` column and deletes that user's rows,
    then deletes the `users` row itself -- at which point every other
    phase's own `ondelete="CASCADE"` foreign keys (declared in each
    table's migration) let MySQL finish cascading through anything this
    walk didn't reach directly (a message under a conversation, a version
    under an asset, a finding under an audit, ...).
    """
    user = await db.get(User, user_id)
    if user is None:
        raise ApiError(ErrorCode.NOT_FOUND, "no such user")

    subscription = (
        await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    ).scalar_one_or_none()
    if subscription is not None and subscription.provider_customer_id:
        provider = get_provider(subscription.provider)
        try:
            await provider.delete_customer(customer_id=subscription.provider_customer_id)
        except BillingProviderError:
            # Don't let a provider-side failure block the user's own
            # deletion -- the local data is gone regardless, and this is
            # logged for a human to reconcile with the provider directly.
            logger.exception(
                "provider_customer_deletion_failed",
                extra={"user_id": str(user_id), "provider": subscription.provider},
            )

    for mapper in Base.registry.mappers:
        model = mapper.class_
        if model is User or not hasattr(model, "user_id"):
            continue
        await db.execute(delete(model).where(model.user_id == user_id))

    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()


async def purge_expired_profile_imports(db: AsyncSession) -> int:
    result = cast(
        CursorResult[Any],
        await db.execute(
            delete(ProfileImportBlob).where(ProfileImportBlob.expires_at <= datetime.now(UTC))
        ),
    )
    await db.commit()
    return result.rowcount or 0


async def purge_expired_ai_cache(db: AsyncSession) -> int:
    result = cast(
        CursorResult[Any],
        await db.execute(delete(AICache).where(AICache.expires_at <= datetime.now(UTC))),
    )
    await db.commit()
    return result.rowcount or 0


async def purge_old_email_logs(db: AsyncSession) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=settings.log_retention_days)
    result = cast(
        CursorResult[Any], await db.execute(delete(EmailLog).where(EmailLog.created_at <= cutoff))
    )
    await db.commit()
    return result.rowcount or 0


async def purge_old_ai_invocations(db: AsyncSession) -> int:
    """`AIInvocation` never stores prompt/completion content (see
    docs/security.md "What never reaches logs") -- what this caps is how
    long the metering metadata itself (tokens, cost, latency, correlation
    id) is kept, per docs/privacy.md. The admin AI-ops dashboard's cost
    trends are only ever queried over the last 30 days, well inside this
    window, so trimming older rows doesn't affect it."""
    cutoff = datetime.now(UTC) - timedelta(days=settings.ai_invocation_payload_retention_days)
    result = cast(
        CursorResult[Any],
        await db.execute(delete(AIInvocation).where(AIInvocation.created_at <= cutoff)),
    )
    await db.commit()
    return result.rowcount or 0


async def purge_expired_data_exports(db: AsyncSession) -> int:
    result = cast(
        CursorResult[Any],
        await db.execute(delete(DataExport).where(DataExport.expires_at <= datetime.now(UTC))),
    )
    await db.commit()
    return result.rowcount or 0


async def find_users_due_for_hard_delete(db: AsyncSession) -> list[uuid.UUID]:
    cutoff = datetime.now(UTC) - timedelta(days=settings.account_hard_delete_after_days)
    result = await db.execute(
        select(User.id).where(User.status == "deleted", User.deleted_at <= cutoff)
    )
    return list(result.scalars().all())
