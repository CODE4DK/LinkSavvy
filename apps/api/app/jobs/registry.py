"""Maps a job's `type` string to the async function that runs it, and
(optionally) to a finer-grained progress calculator than the generic
status-based fallback."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.models.job import Job

# `session_factory` is the same one `run_once` was given -- a handler that
# needs to fan work out across concurrent coroutines (the audit
# orchestrator running its five categories, say) can open one session per
# coroutine from it rather than sharing the single `db` session, which
# isn't safe to use from more than one coroutine at a time.
JobHandler = Callable[[Job, AsyncSession, SessionFactory], Awaitable[dict[str, Any] | None]]
ProgressCalculator = Callable[[Job, AsyncSession], Awaitable[int]]

_HANDLERS: dict[str, JobHandler] = {}
_PROGRESS_CALCULATORS: dict[str, ProgressCalculator] = {}


class UnknownJobType(Exception):
    def __init__(self, job_type: str) -> None:
        super().__init__(f"no handler registered for job type {job_type!r}")


def register_handler(job_type: str) -> Callable[[JobHandler], JobHandler]:
    def decorator(handler: JobHandler) -> JobHandler:
        if job_type in _HANDLERS:
            raise ValueError(f"a handler is already registered for job type {job_type!r}")
        _HANDLERS[job_type] = handler
        return handler

    return decorator


def get_handler(job_type: str) -> JobHandler:
    try:
        return _HANDLERS[job_type]
    except KeyError as exc:
        raise UnknownJobType(job_type) from exc


def register_progress_calculator(
    job_type: str,
) -> Callable[[ProgressCalculator], ProgressCalculator]:
    def decorator(calculator: ProgressCalculator) -> ProgressCalculator:
        _PROGRESS_CALCULATORS[job_type] = calculator
        return calculator

    return decorator


async def compute_progress(job: Job, db: AsyncSession) -> int:
    if job.status in ("succeeded", "failed", "dead"):
        return 100
    if job.status == "queued":
        return 0
    calculator = _PROGRESS_CALCULATORS.get(job.type)
    if calculator is None:
        return 50  # leased with no type-specific signal: "in progress"
    return await calculator(job, db)
