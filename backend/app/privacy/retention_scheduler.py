"""The one process that actually enforces docs/privacy.md's retention
windows: hard-deletes accounts past their grace period and sweeps every
other time-boxed table. Runs on a plain interval (not the weekly/Monday
shape of the other schedulers in this codebase) since retention is a
"how much has piled up since last time" job, not a calendar event.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal, SessionFactory
from app.privacy.purge import (
    find_users_due_for_hard_delete,
    hard_delete_user,
    purge_expired_ai_cache,
    purge_expired_data_exports,
    purge_expired_profile_imports,
    purge_old_ai_invocations,
    purge_old_email_logs,
)
from app.workspace.assets import purge_expired_trash

logger = logging.getLogger("app.privacy.retention_scheduler")

DEFAULT_POLL_INTERVAL_SECONDS = 3600.0


async def run_once(db: AsyncSession) -> dict[str, int]:
    due_user_ids = await find_users_due_for_hard_delete(db)
    for user_id in due_user_ids:
        await hard_delete_user(db, user_id=user_id)

    return {
        "hard_deleted_users": len(due_user_ids),
        "expired_profile_imports": await purge_expired_profile_imports(db),
        "expired_ai_cache": await purge_expired_ai_cache(db),
        "old_email_logs": await purge_old_email_logs(db),
        "old_ai_invocations": await purge_old_ai_invocations(db),
        "expired_asset_trash": await purge_expired_trash(db),
        "expired_data_exports": await purge_expired_data_exports(db),
    }


async def run_scheduler(
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    iterations: int | None = None,
    session_factory: SessionFactory = AsyncSessionLocal,
) -> None:
    count = 0
    while iterations is None or count < iterations:
        async with session_factory() as db:
            counts = await run_once(db)
            if any(counts.values()):
                logger.info("retention_sweep", extra=counts)
        count += 1
        if iterations is None or count < iterations:
            await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    asyncio.run(run_scheduler())
