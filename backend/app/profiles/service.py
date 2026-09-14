"""The profile data layer's write path.

`commit_snapshot` is the one function every input path (LinkedIn sync,
paste, upload, manual form) converges on to actually persist a
ProfileSnapshot. Nothing else writes to `profile_snapshots`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile_import import ProfileImportBlob
from app.models.profile_snapshot import ProfileSnapshotRow
from app.models.user import User
from app.profiles.completeness import compute_completeness
from app.profiles.schema import ProfileSnapshot, ProfileSource
from app.security.crypto import encrypt_bytes
from app.services.audit import record_audit_event
from app.settings import settings


async def store_raw_input(
    db: AsyncSession, *, content: bytes, content_type: str
) -> ProfileImportBlob:
    """Encrypts and stores the raw paste/upload content a profile_imports
    row will point at (raw_input_ref). Stands in for real object storage —
    see docs/adr/0003."""
    now = datetime.now(UTC)
    blob = ProfileImportBlob(
        ciphertext=encrypt_bytes(content),
        content_type=content_type,
        created_at=now,
        expires_at=now + timedelta(days=settings.profile_import_retention_days),
    )
    db.add(blob)
    await db.flush()
    return blob


async def _next_version(db: AsyncSession, *, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(func.max(ProfileSnapshotRow.version)).where(ProfileSnapshotRow.user_id == user_id)
    )
    current_max = result.scalar_one_or_none()
    return (current_max or 0) + 1


async def commit_snapshot(
    db: AsyncSession, *, user: User, payload: ProfileSnapshot, source: ProfileSource
) -> ProfileSnapshotRow:
    """Validates, scores, versions, and activates a new ProfileSnapshot.

    This is the only function that writes to `profile_snapshots` — every
    input path (LinkedIn sync, paste, upload, manual) calls this, passing
    its own `source`, which always wins over whatever `payload.source` a
    client happened to send.
    """
    snapshot = payload.model_copy(update={"source": source})
    completeness = compute_completeness(snapshot)
    version = await _next_version(db, user_id=user.id)

    await db.execute(
        update(ProfileSnapshotRow)
        .where(ProfileSnapshotRow.user_id == user.id, ProfileSnapshotRow.is_active.is_(True))
        .values(is_active=False)
    )

    row = ProfileSnapshotRow(
        user_id=user.id,
        version=version,
        source=source.value,
        payload=snapshot.model_dump(mode="json"),
        completeness_score=completeness.score,
        captured_at=snapshot.captured_at,
        is_active=True,
    )
    db.add(row)
    await db.flush()

    await record_audit_event(
        db,
        actor_user_id=user.id,
        action="profile.commit_snapshot",
        target_type="profile_snapshot",
        target_id=str(row.id),
        metadata={
            "version": version,
            "source": source.value,
            "completeness_score": completeness.score,
        },
    )
    return row


async def get_active_snapshot(db: AsyncSession, *, user_id: uuid.UUID) -> ProfileSnapshotRow | None:
    result = await db.execute(
        select(ProfileSnapshotRow).where(
            ProfileSnapshotRow.user_id == user_id, ProfileSnapshotRow.is_active.is_(True)
        )
    )
    return result.scalar_one_or_none()


async def list_snapshots(db: AsyncSession, *, user_id: uuid.UUID) -> list[ProfileSnapshotRow]:
    result = await db.execute(
        select(ProfileSnapshotRow)
        .where(ProfileSnapshotRow.user_id == user_id)
        .order_by(ProfileSnapshotRow.version.desc())
    )
    return list(result.scalars().all())


async def get_snapshot_by_version(
    db: AsyncSession, *, user_id: uuid.UUID, version: int
) -> ProfileSnapshotRow | None:
    result = await db.execute(
        select(ProfileSnapshotRow).where(
            ProfileSnapshotRow.user_id == user_id, ProfileSnapshotRow.version == version
        )
    )
    return result.scalar_one_or_none()
