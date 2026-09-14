from __future__ import annotations

import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.audit import job_handler  # noqa: F401 -- registers the "audit" job handler
from app.jobs.queue import enqueue
from app.jobs.worker import run_once
from app.models.audit import Audit, AuditCategoryResult
from app.models.content_plan import ContentPlan
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


async def test_content_category_stops_skipping_once_the_user_has_posted_content(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    await commit_snapshot(
        db_session, user=user, payload=rich_snapshot(), source=ProfileSource.MANUAL
    )
    db_session.add(
        ContentPlan(
            user_id=user.id,
            body_preview="A real post I published on LinkedIn about my work.",
            status="posted",
            planned_for=datetime.date(2026, 6, 1),
        )
    )
    await db_session.commit()

    job = await enqueue(
        db_session, job_type="audit", payload={"trigger": "manual"}, user_id=user.id
    )
    processed = await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    assert processed is True

    audit_id = (
        await db_session.execute(select(Audit.id).where(Audit.job_id == job.id))
    ).scalar_one()
    content_result = (
        await db_session.execute(
            select(AuditCategoryResult).where(
                AuditCategoryResult.audit_id == audit_id,
                AuditCategoryResult.category == "content",
            )
        )
    ).scalar_one()
    assert content_result.status != "skipped"
