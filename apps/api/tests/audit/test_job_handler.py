from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.audit import job_handler  # noqa: F401 -- registers the "audit" job handler
from app.jobs.queue import enqueue
from app.jobs.worker import run_once
from app.models.job import Job
from app.models.user import User
from app.profiles.schema import ProfileSource
from app.profiles.service import commit_snapshot

from .categories.conftest import rich_snapshot


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"audit-job-{uuid.uuid4()}@example.com", full_name="Audit Job Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_audit_job_runs_the_orchestrator_and_succeeds(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    await db_session.commit()

    job = await enqueue(
        db_session, job_type="audit", payload={"trigger": "manual"}, user_id=user.id
    )

    processed = await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    assert processed is True

    reloaded = await db_session.get(Job, job.id, populate_existing=True)
    assert reloaded is not None
    assert reloaded.status == "succeeded"
    assert reloaded.result is not None
    assert reloaded.result["status"] in ("completed", "completed_with_errors")


async def test_audit_job_fails_without_an_active_snapshot(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    job = await enqueue(
        db_session, job_type="audit", payload={"trigger": "manual"}, user_id=user.id, max_attempts=1
    )

    processed = await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    assert processed is True

    reloaded = await db_session.get(Job, job.id, populate_existing=True)
    assert reloaded is not None
    assert reloaded.status == "dead"
    assert reloaded.error is not None and "no active profile snapshot" in reloaded.error
