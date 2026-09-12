from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.jobs.queue import enqueue
from app.jobs.registry import register_handler
from app.jobs.worker import run_worker
from app.models.job import Job
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"loop-{uuid.uuid4()}@example.com", full_name="Loop Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_run_worker_processes_all_queued_jobs_then_idles(
    db_session: AsyncSession, db_sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    calls: list[str] = []

    @register_handler("test.loop.marker")
    async def handler(job: Job, db: AsyncSession) -> None:
        calls.append(str(job.id))

    user = await _create_user(db_session)
    await enqueue(db_session, job_type="test.loop.marker", payload={}, user_id=user.id)
    await enqueue(db_session, job_type="test.loop.marker", payload={}, user_id=user.id)

    # 3 iterations: 2 real jobs + 1 that finds the queue empty and sleeps.
    await run_worker(
        worker_id="loop-tester",
        iterations=3,
        poll_interval=0.01,
        session_factory=db_sessionmaker,
    )

    assert len(calls) == 2
