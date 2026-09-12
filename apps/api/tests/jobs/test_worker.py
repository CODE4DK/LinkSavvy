from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.jobs.queue import enqueue
from app.jobs.registry import register_handler
from app.jobs.worker import lease_next_job, reclaim_expired_leases, run_once
from app.models.base import Base
from app.models.job import Job
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"worker-{uuid.uuid4()}@example.com", full_name="Worker Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_lease_next_job_claims_highest_priority_first(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await enqueue(db_session, job_type="noop", payload={}, user_id=user.id, priority=0)
    high = await enqueue(db_session, job_type="noop", payload={}, user_id=user.id, priority=10)

    leased = await lease_next_job(db_session, worker_id="w1")
    assert leased is not None
    assert leased.id == high.id
    assert leased.status == "leased"
    assert leased.worker_id == "w1"
    assert leased.attempts == 1
    assert leased.started_at is not None
    assert leased.lease_expires_at is not None


async def test_lease_next_job_ignores_future_scheduled_jobs(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    await enqueue(
        db_session,
        job_type="noop",
        payload={},
        user_id=user.id,
        scheduled_for=datetime.now(UTC) + timedelta(hours=1),
    )
    leased = await lease_next_job(db_session, worker_id="w1")
    assert leased is None


async def test_lease_next_job_returns_none_when_empty(db_session: AsyncSession) -> None:
    assert await lease_next_job(db_session, worker_id="w1") is None


async def test_started_at_is_set_once_across_retries(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    job = await enqueue(db_session, job_type="noop", payload={}, user_id=user.id)
    first = await lease_next_job(db_session, worker_id="w1")
    assert first is not None
    first_started_at = first.started_at

    # simulate a retry: put it back to queued, as _record_failure would
    job.status = "queued"
    job.lease_expires_at = None
    job.worker_id = None
    await db_session.commit()

    second = await lease_next_job(db_session, worker_id="w2")
    assert second is not None
    assert second.started_at == first_started_at


async def test_reclaim_expired_leases_requeues_stale_jobs(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    job = await enqueue(db_session, job_type="noop", payload={}, user_id=user.id)
    job.status = "leased"
    job.worker_id = "dead-worker"
    job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await db_session.commit()

    reclaimed = await reclaim_expired_leases(db_session)
    assert reclaimed == 1

    await db_session.refresh(job)
    assert job.status == "queued"
    assert job.worker_id is None
    assert job.lease_expires_at is None


async def test_run_once_marks_success_and_stores_result(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    @register_handler("test.worker.success")
    async def handler(job: Job, db: AsyncSession) -> dict[str, int]:
        return {"answer": 42}

    user = await _create_user(db_session)
    job = await enqueue(db_session, job_type="test.worker.success", payload={}, user_id=user.id)

    processed = await run_once(worker_id="w1", session_factory=db_sessionmaker)
    assert processed is True

    row = await db_session.get(Job, job.id, populate_existing=True)
    assert row is not None
    assert row.status == "succeeded"
    assert row.result == {"answer": 42}
    assert row.finished_at is not None


async def test_run_once_retries_on_failure_with_backoff(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    @register_handler("test.worker.fails_then_would_retry")
    async def handler(job: Job, db: AsyncSession) -> None:
        raise RuntimeError("boom")

    user = await _create_user(db_session)
    job = await enqueue(
        db_session,
        job_type="test.worker.fails_then_would_retry",
        payload={},
        user_id=user.id,
        max_attempts=3,
    )

    before = datetime.now(UTC)
    processed = await run_once(worker_id="w1", session_factory=db_sessionmaker)
    assert processed is True

    row = await db_session.get(Job, job.id, populate_existing=True)
    assert row is not None
    assert row.status == "queued"
    assert row.attempts == 1
    assert row.error is not None and "boom" in row.error
    assert row.scheduled_for > before


async def test_run_once_dead_letters_after_max_attempts(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    @register_handler("test.worker.always_fails")
    async def handler(job: Job, db: AsyncSession) -> None:
        raise RuntimeError("permanent failure")

    user = await _create_user(db_session)
    job = await enqueue(
        db_session, job_type="test.worker.always_fails", payload={}, user_id=user.id, max_attempts=1
    )

    processed = await run_once(worker_id="w1", session_factory=db_sessionmaker)
    assert processed is True

    row = await db_session.get(Job, job.id, populate_existing=True)
    assert row is not None
    assert row.status == "dead"
    assert row.finished_at is not None


async def test_run_once_handles_unknown_job_type_without_crashing(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    user = await _create_user(db_session)
    job = await enqueue(
        db_session,
        job_type="no.such.handler.registered",
        payload={},
        user_id=user.id,
        max_attempts=1,
    )

    processed = await run_once(worker_id="w1", session_factory=db_sessionmaker)
    assert processed is True

    row = await db_session.get(Job, job.id, populate_existing=True)
    assert row is not None
    assert row.status == "dead"
    assert row.error is not None


async def test_concurrent_lease_attempts_never_double_claim_one_job() -> None:
    """Mirrors the quota concurrency test's shape: many workers racing for
    the one available job must result in exactly one winner."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_maker() as setup:
        user = User(email="racer@example.com", full_name="Racer")
        setup.add(user)
        await setup.commit()
        await setup.refresh(user)
        user_id = user.id
        job = await enqueue(setup, job_type="noop", payload={}, user_id=user_id)
        job_id = job.id

    async def attempt(worker_id: str) -> bool:
        async with session_maker() as session:
            leased = await lease_next_job(session, worker_id=worker_id)
            return leased is not None and leased.id == job_id

    results = await asyncio.gather(*(attempt(f"w{i}") for i in range(20)))
    assert sum(results) == 1

    await engine.dispose()
