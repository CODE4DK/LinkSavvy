from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import platform_health
from app.ai.circuit_breaker import circuit_breaker
from app.jobs.queue import enqueue
from app.models.user import User


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(
        email=f"health-test-{uuid.uuid4()}@example.com", full_name="Health Tester", **kwargs
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_queue_depth_counts_by_status(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await enqueue(db_session, job_type="audit", payload={}, user_id=user.id)
    depth = await platform_health.queue_depth(db_session)
    assert depth.queued >= 1


async def test_retry_dead_job_requeues_it(db_session: AsyncSession) -> None:
    admin = await _create_user(db_session, role="admin")
    user = await _create_user(db_session)
    job = await enqueue(db_session, job_type="audit", payload={}, user_id=user.id)
    job.status = "dead"
    job.attempts = 5
    job.error = "boom"
    job.finished_at = datetime.now(UTC)
    await db_session.commit()

    retried = await platform_health.retry_dead_job(db_session, admin_id=admin.id, job_id=job.id)
    assert retried.status == "queued"
    assert retried.attempts == 0
    assert retried.error is None


async def test_provider_circuit_state_reflects_recorded_failures() -> None:
    circuit_breaker.record_failure("test-provider")
    snapshot = platform_health.provider_circuit_state()
    assert "test-provider" in snapshot
    circuit_breaker.record_success("test-provider")
