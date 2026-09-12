"""Async database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.settings import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

# Shared type for code that opens its own session(s) rather than being
# handed one -- the background job worker (concurrent per-job sessions)
# and the audit orchestrator (one session per concurrently-run category,
# since AsyncSession isn't safe to share across concurrent coroutines)
# both take one of these, defaulting to AsyncSessionLocal in production
# and a test's isolated in-memory sessionmaker otherwise.
SessionFactory = Callable[[], AsyncSession]


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
