"""enqueue() is the only way application code creates a job row — never
construct a `Job` directly outside this module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job

DEFAULT_MAX_ATTEMPTS = 5


async def enqueue(
    db: AsyncSession,
    *,
    job_type: str,
    payload: dict[str, Any],
    user_id: uuid.UUID,
    scheduled_for: datetime | None = None,
    priority: int = 0,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> Job:
    job = Job(
        user_id=user_id,
        type=job_type,
        payload=payload,
        scheduled_for=scheduled_for or datetime.now(UTC),
        priority=priority,
        max_attempts=max_attempts,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job
