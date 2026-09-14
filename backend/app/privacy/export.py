"""Composes `POST /me/export`'s ZIP: one JSON file per table that has a
direct `user_id` column, covering every phase's data without a
hand-maintained list that goes stale the next time a phase adds a table.

Never includes a live secret. `_SENSITIVE_COLUMNS` is excluded from every
table rather than decrypted back to plaintext -- a downloadable ZIP is a
bigger blast radius than the database itself, so an OAuth access token or
password hash never rides along even though the user technically "owns"
it.

The raw text/file behind a profile import (app.models.profile_import
.ProfileImportBlob) is deliberately not included: it has no direct
`user_id` column for this generic walk to find it through (it's reached
via `profile_imports.raw_input_ref`), and it is transient by design --
`settings.profile_import_retention_days` -- while the parsed
ProfileSnapshot it produced is permanent and *is* included, via
`profile_snapshot_rows` and `profile_imports` themselves.
"""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from datetime import date, datetime
from typing import Any

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.models.user import User

_SENSITIVE_COLUMNS = frozenset(
    {
        "password_hash",
        "access_token_encrypted",
        "refresh_token_encrypted",
        "token_hash",
    }
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, bytes):
        return None  # binary blobs (e.g. encrypted zips) are never included
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _row_to_dict(model: type[Base], row: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in inspect(model).columns:
        if column.name in _SENSITIVE_COLUMNS:
            continue
        result[column.name] = _json_safe(getattr(row, column.name))
    return result


async def compose_export_zip(db: AsyncSession, *, user: User) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "account.json",
            json.dumps(_row_to_dict(User, user), indent=2, default=str),
        )

        for mapper in Base.registry.mappers:
            model = mapper.class_
            if model is User or not hasattr(model, "user_id"):
                continue
            rows = (await db.execute(select(model).where(model.user_id == user.id))).scalars().all()
            if not rows:
                continue
            archive.writestr(
                f"{model.__tablename__}.json",
                json.dumps([_row_to_dict(model, row) for row in rows], indent=2, default=str),
            )

        archive.writestr(
            "README.txt",
            "This export contains every record LinkSavvy stores about your account.\n"
            "Live credentials (password hash, OAuth tokens, password-reset tokens) are\n"
            "deliberately excluded -- see docs/privacy.md for why.\n",
        )
    return buffer.getvalue()
