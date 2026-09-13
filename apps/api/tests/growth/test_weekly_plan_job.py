from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.growth.weekly_plan_job import generate_weekly_plan
from app.jobs.queue import enqueue
from app.models.job import Job
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"growth-job-{uuid.uuid4()}@example.com", full_name="Job Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_generates_a_plan_for_the_job_users(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    job = await enqueue(db_session, job_type="weekly_plan.generate", payload={}, user_id=user.id)

    result = await generate_weekly_plan(job, db_session, AsyncSessionLocal)

    assert result is not None
    assert result["item_count"] == 0
    assert "weekly_plan_id" in result


async def test_skips_when_the_user_no_longer_exists(db_session: AsyncSession) -> None:
    fake_job = Job(
        user_id=uuid.uuid4(),
        type="weekly_plan.generate",
        payload={},
        scheduled_for=datetime.now(UTC),
    )
    db_session.add(fake_job)
    await db_session.commit()
    await db_session.refresh(fake_job)

    result = await generate_weekly_plan(fake_job, db_session, AsyncSessionLocal)
    assert result == {"skipped": "user no longer exists"}
