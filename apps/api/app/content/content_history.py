"""Resolves `AuditContext.content_history` for a user who never
explicitly supplied one on the audit request -- the Content audit
category (app/audit/categories/content.py) only ever saw `None` before
Content Hub existed, since there was no posting history anywhere in
the system to fall back to. Now there is: the user's own posted
`content_plans` and any `content_samples` they gave the voice profile
are both genuine content history, so a client that doesn't pass
`content_history` explicitly gets one built from those instead of
silently skipping the category.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_plan import ContentPlan
from app.models.content_sample import ContentSample


async def resolve_content_history(
    db: AsyncSession, *, user_id: uuid.UUID, explicit: list[str] | None
) -> list[str] | None:
    if explicit:
        return explicit

    posted = (
        await db.execute(
            select(ContentPlan.body_preview).where(
                ContentPlan.user_id == user_id,
                ContentPlan.status == "posted",
                ContentPlan.deleted_at.is_(None),
            )
        )
    ).scalars()
    samples = (
        await db.execute(
            select(ContentSample.body).where(
                ContentSample.user_id == user_id, ContentSample.deleted_at.is_(None)
            )
        )
    ).scalars()

    texts = [text for text in (*posted, *samples) if text and text.strip()]
    return texts or None
