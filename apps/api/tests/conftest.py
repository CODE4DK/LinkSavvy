"""Test fixtures.

Required settings must exist before `app.settings` (and anything that
imports it) is first imported, so the environment is populated at the
very top of this module, before any `app.*` import.
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-at-least-32-bytes-long")
os.environ.setdefault("REFRESH_TOKEN_PEPPER", "test-refresh-pepper-value")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "1025")

from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.feature_flag import FeatureFlag  # noqa: E402
from app.services.feature_flags import ALL_DEFAULT_FLAG_KEYS  # noqa: E402


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_maker() as seed_session:
        for key in ALL_DEFAULT_FLAG_KEYS:
            seed_session.add(FeatureFlag(key=key, enabled_globally=False, rollout_percent=0))
        await seed_session.commit()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with session_maker() as session:
            yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    # https:// (not http://) so the client's cookie jar will store and
    # resend our Secure refresh-token cookie between requests.
    async with AsyncClient(transport=transport, base_url="https://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient, sent_emails: list[dict[str, str]]) -> dict[str, str]:
    """Registers and verifies a user, returning their credentials."""
    email = "person@example.com"
    password = "correct-horse-99"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Person One"},
    )
    token = next(e["token"] for e in sent_emails if e["kind"] == "verify")
    await client.post("/api/v1/auth/verify-email", json={"token": token})
    return {"email": email, "password": password}


@pytest.fixture(autouse=True)
def _fake_ai_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test gets `FakeProvider` in place of a real OpenAI/Gemini call
    (see app/ai/providers/fake_provider.py and .../registry.py) — this is
    what guarantees the whole suite runs with zero network calls, without
    every test needing to remember to patch it itself."""
    from app.ai.providers import registry
    from app.ai.providers.fake_provider import FakeProvider

    registry._build_provider.cache_clear()
    monkeypatch.setitem(registry._PROVIDER_CLASSES, "openai", FakeProvider)
    monkeypatch.setitem(registry._PROVIDER_CLASSES, "gemini", FakeProvider)
    yield
    registry._build_provider.cache_clear()


@pytest.fixture
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Captures verification/reset emails instead of sending them."""
    captured: list[dict[str, str]] = []

    async def fake_verification(*, to: str, token: str) -> None:
        captured.append({"kind": "verify", "to": to, "token": token})

    async def fake_reset(*, to: str, token: str) -> None:
        captured.append({"kind": "reset", "to": to, "token": token})

    monkeypatch.setattr("app.routers.auth.send_verification_email", fake_verification)
    monkeypatch.setattr("app.routers.auth.send_password_reset_email", fake_reset)
    return captured
