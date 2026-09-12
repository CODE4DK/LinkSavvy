from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.queue import enqueue
from app.jobs.registry import (
    UnknownJobType,
    compute_progress,
    get_handler,
    register_handler,
    register_progress_calculator,
)
from app.models.job import Job
from app.models.user import User


async def _create_user(db: AsyncSession) -> User:
    user = User(email=f"jobs-{uuid.uuid4()}@example.com", full_name="Jobs Tester")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_enqueue_sets_expected_defaults(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    job = await enqueue(db_session, job_type="noop", payload={"a": 1}, user_id=user.id)
    assert job.status == "queued"
    assert job.attempts == 0
    assert job.max_attempts == 5
    assert job.priority == 0
    assert job.payload == {"a": 1}
    assert job.scheduled_for is not None


def test_get_handler_raises_for_unregistered_type() -> None:
    with pytest.raises(UnknownJobType):
        get_handler("no.such.type.ever.registered")


def test_register_handler_rejects_duplicate_registration() -> None:
    @register_handler("test.duplicate.unique.marker")
    async def handler_one(job: Job, db: AsyncSession) -> None:
        return None

    with pytest.raises(ValueError, match="already registered"):

        @register_handler("test.duplicate.unique.marker")
        async def handler_two(job: Job, db: AsyncSession) -> None:
            return None


async def test_compute_progress_defaults_by_status(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    job = await enqueue(
        db_session, job_type="unregistered.progress.type", payload={}, user_id=user.id
    )
    assert await compute_progress(job, db_session) == 0

    job.status = "leased"
    assert await compute_progress(job, db_session) == 50

    job.status = "succeeded"
    assert await compute_progress(job, db_session) == 100

    job.status = "dead"
    assert await compute_progress(job, db_session) == 100


async def test_compute_progress_uses_registered_calculator(db_session: AsyncSession) -> None:
    @register_progress_calculator("test.custom.progress.marker")
    async def calculator(job: Job, db: AsyncSession) -> int:
        return 42

    user = await _create_user(db_session)
    job = await enqueue(
        db_session, job_type="test.custom.progress.marker", payload={}, user_id=user.id
    )
    job.status = "leased"
    assert await compute_progress(job, db_session) == 42
