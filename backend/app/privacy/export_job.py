"""The `privacy.export` job: composes the ZIP (app/privacy/export.py),
encrypts it at rest, and notifies the user it's ready to download.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionFactory
from app.jobs.queue import enqueue
from app.jobs.registry import register_handler
from app.models.data_export import DataExport
from app.models.job import Job
from app.models.user import User
from app.notifications.dispatch_job import DISPATCH_JOB_TYPE
from app.privacy.export import compose_export_zip
from app.security.crypto import encrypt_bytes

EXPORT_JOB_TYPE = "privacy.export"
_EXPORT_TTL_DAYS = 7


@register_handler(EXPORT_JOB_TYPE)
async def generate_data_export(
    job: Job, db: AsyncSession, session_factory: SessionFactory
) -> dict[str, Any] | None:
    user = await db.get(User, job.user_id)
    if user is None:
        return {"skipped": "user no longer exists"}

    zip_bytes = await compose_export_zip(db, user=user)
    export = DataExport(
        user_id=user.id,
        encrypted_zip=encrypt_bytes(zip_bytes),
        expires_at=datetime.now(UTC) + timedelta(days=_EXPORT_TTL_DAYS),
    )
    db.add(export)
    await db.commit()
    await db.refresh(export)

    await enqueue(
        db,
        job_type=DISPATCH_JOB_TYPE,
        payload={
            "type": "privacy.export_ready",
            "title": "Your data export is ready",
            "body": f"Download it within {_EXPORT_TTL_DAYS} days -- the link expires after that.",
            "action_route": f"/settings/export/{export.id}",
        },
        user_id=user.id,
    )
    return {"export_id": str(export.id), "size_bytes": len(zip_bytes)}
