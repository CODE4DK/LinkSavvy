from __future__ import annotations

import io
import json
import uuid
import zipfile

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.user import User
from app.privacy.export import compose_export_zip


async def _create_user(db: AsyncSession, **kwargs: object) -> User:
    user = User(
        email=f"export-{uuid.uuid4()}@example.com",
        full_name="Export Tester",
        password_hash="super-secret-hash",
        **kwargs,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_export_includes_account_and_owned_data(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    db_session.add(
        Asset(user_id=user.id, type="post", title="My headline draft", body="body text", tags=[])
    )
    await db_session.commit()

    zip_bytes = await compose_export_zip(db_session, user=user)
    archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = archive.namelist()

    assert "account.json" in names
    assert "assets.json" in names

    account = json.loads(archive.read("account.json"))
    assert account["email"] == user.email
    assert "password_hash" not in account

    assets = json.loads(archive.read("assets.json"))
    assert assets[0]["title"] == "My headline draft"


async def test_export_omits_empty_tables(db_session: AsyncSession) -> None:
    user = await _create_user(db_session)
    zip_bytes = await compose_export_zip(db_session, user=user)
    archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert "assets.json" not in archive.namelist()
