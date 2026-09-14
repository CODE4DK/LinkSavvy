"""The `jobs` table's worker loop: lease, run, heartbeat, retry with
jittered backoff, dead-letter after `max_attempts`. No Celery, no Redis —
this loop and the table are the entire background-job system, per
CLAUDE.md's stack rule.

Run it with `python -m app.jobs.worker` (see `make worker`).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import socket
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.redact import redact_text
from app.db import AsyncSessionLocal, SessionFactory
from app.jobs.registry import UnknownJobType, get_handler
from app.models.job import Job

logger = logging.getLogger("app.jobs.worker")

DEFAULT_LEASE_SECONDS = 120.0
DEFAULT_POLL_INTERVAL_SECONDS = 2.0
BASE_BACKOFF_SECONDS = 10.0
MAX_ERROR_LENGTH = 2000
_MAX_LEASE_RACE_RETRIES = 10


def new_worker_id() -> str:
    return f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"


async def reclaim_expired_leases(db: AsyncSession) -> int:
    """A leased job whose lease has expired (its worker crashed or was
    killed mid-job) goes back to 'queued' so another worker can pick it
    up. Called at worker startup and at the top of every poll cycle."""
    now = datetime.now(UTC)
    result = await db.execute(
        update(Job)
        .where(Job.status == "leased", Job.lease_expires_at < now)
        .values(status="queued", lease_expires_at=None, worker_id=None)
    )
    await db.commit()
    return cast(CursorResult[Any], result).rowcount or 0


async def _select_candidate(db: AsyncSession) -> uuid.UUID | None:
    now = datetime.now(UTC)
    candidate: uuid.UUID | None = (
        await db.execute(
            select(Job.id)
            .where(Job.status == "queued", Job.scheduled_for <= now)
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return candidate


async def lease_next_job(
    db: AsyncSession, *, worker_id: str, lease_seconds: float = DEFAULT_LEASE_SECONDS
) -> Job | None:
    """Atomically claims the highest-priority, oldest eligible queued job.

    A SELECT candidate + conditional UPDATE (WHERE id=... AND
    status='queued') rather than `UPDATE ... ORDER BY ... LIMIT 1`:  the
    latter isn't portable to SQLite (used by the test suite), and the
    conditional UPDATE is just as safe under real concurrency — if
    another worker's lease attempt wins the race between our SELECT and
    UPDATE, our rowcount is 0 and we simply try the next candidate.
    """
    now = datetime.now(UTC)
    lease_expires_at = now + timedelta(seconds=lease_seconds)
    for _ in range(_MAX_LEASE_RACE_RETRIES):
        candidate_id = await _select_candidate(db)
        if candidate_id is None:
            return None
        result = await db.execute(
            update(Job)
            .where(Job.id == candidate_id, Job.status == "queued")
            .values(
                status="leased",
                worker_id=worker_id,
                lease_expires_at=lease_expires_at,
                # Set once, on the first lease -- left alone on a retry so
                # it always reflects when work first began, not the most
                # recent attempt.
                started_at=func.coalesce(Job.started_at, now),
                attempts=Job.attempts + 1,
            )
        )
        if cast(CursorResult[Any], result).rowcount:
            await db.commit()
            # populate_existing: the UPDATE above used server-side
            # expressions (func.coalesce, Job.attempts + 1) that the ORM
            # can't evaluate client-side, so it expires those attributes
            # on any already-identity-mapped copy of this row rather than
            # guessing their new values -- a plain db.get() would return
            # that same (attribute-expired) object, and a later bare
            # attribute access outside of an awaited context would try to
            # lazy-load synchronously and crash under asyncio.
            job = await db.get(Job, candidate_id, populate_existing=True)
            assert job is not None
            return job
        await db.rollback()
    return None


async def _heartbeat_loop(
    job_id: uuid.UUID, *, worker_id: str, lease_seconds: float, session_factory: SessionFactory
) -> None:
    """Periodically extends the lease while a job is being worked, so a
    slow-but-alive job never gets reclaimed out from under its worker."""
    try:
        while True:
            await asyncio.sleep(lease_seconds / 2)
            async with session_factory() as hb_db:
                await hb_db.execute(
                    update(Job)
                    .where(Job.id == job_id, Job.worker_id == worker_id, Job.status == "leased")
                    .values(lease_expires_at=datetime.now(UTC) + timedelta(seconds=lease_seconds))
                )
                await hb_db.commit()
    except asyncio.CancelledError:
        raise


async def _record_success(
    db: AsyncSession, job_id: uuid.UUID, *, result: dict[str, Any] | None
) -> None:
    await db.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(status="succeeded", finished_at=datetime.now(UTC), result=result, error=None)
    )
    await db.commit()


async def _record_failure(db: AsyncSession, job: Job, *, error: str) -> None:
    now = datetime.now(UTC)
    truncated_error = error[:MAX_ERROR_LENGTH]
    if job.attempts < job.max_attempts:
        backoff = BASE_BACKOFF_SECONDS * (2 ** (job.attempts - 1)) + random.uniform(  # nosec B311
            0, BASE_BACKOFF_SECONDS
        )
        await db.execute(
            update(Job)
            .where(Job.id == job.id)
            .values(
                status="queued",
                lease_expires_at=None,
                worker_id=None,
                scheduled_for=now + timedelta(seconds=backoff),
                error=truncated_error,
            )
        )
    else:
        await db.execute(
            update(Job)
            .where(Job.id == job.id)
            .values(status="dead", finished_at=now, error=truncated_error)
        )
    await db.commit()


async def run_once(
    *,
    worker_id: str,
    lease_seconds: float = DEFAULT_LEASE_SECONDS,
    session_factory: SessionFactory = AsyncSessionLocal,
) -> bool:
    """Leases and fully processes at most one job. Returns True if a job
    was found and processed (successfully or not), False if the queue was
    empty. `session_factory` defaults to the real app database — tests
    pass their own isolated one."""
    async with session_factory() as db:
        await reclaim_expired_leases(db)
        job = await lease_next_job(db, worker_id=worker_id, lease_seconds=lease_seconds)
        if job is None:
            return False

        try:
            handler = get_handler(job.type)
        except UnknownJobType as exc:
            await _record_failure(db, job, error=str(exc))
            return True

        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(
                job.id,
                worker_id=worker_id,
                lease_seconds=lease_seconds,
                session_factory=session_factory,
            )
        )
        succeeded = False
        result: dict[str, Any] | None = None
        error_message = ""
        try:
            result = await handler(job, db, session_factory)
            succeeded = True
        except (
            Exception
        ) as exc:  # noqa: BLE001 -- any handler failure must retry/dead-letter, never crash the worker loop
            error_message = str(exc)
            logger.warning(
                "job_handler_failed",
                extra={
                    "job_id": str(job.id),
                    "job_type": job.type,
                    "attempts": job.attempts,
                    "error_summary": redact_text(error_message),
                },
            )
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

        if succeeded:
            await _record_success(db, job.id, result=result)
        else:
            await _record_failure(db, job, error=error_message)
        return True


async def run_worker(
    *,
    worker_id: str | None = None,
    lease_seconds: float = DEFAULT_LEASE_SECONDS,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    iterations: int | None = None,
    session_factory: SessionFactory = AsyncSessionLocal,
) -> None:
    """The long-running loop. `iterations=None` runs forever (real
    deployment); a finite `iterations` is what tests pass to run a bounded
    number of poll cycles."""
    resolved_worker_id = worker_id or new_worker_id()
    logger.info("worker_started", extra={"worker_id": resolved_worker_id})
    count = 0
    while iterations is None or count < iterations:
        processed = await run_once(
            worker_id=resolved_worker_id,
            lease_seconds=lease_seconds,
            session_factory=session_factory,
        )
        count += 1
        if not processed:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    # Importing a handler module is what runs its @register_handler
    # decorator -- the worker process needs every job type it might lease
    # registered before it starts polling, which nothing else guarantees.
    from app.audit import job_handler  # noqa: F401
    from app.content import calendar_reminder_job  # noqa: F401
    from app.growth import weekly_plan_job  # noqa: F401
    from app.notifications import dispatch_job, weekly_digest_job  # noqa: F401
    from app.privacy import export_job  # noqa: F401

    asyncio.run(run_worker())
