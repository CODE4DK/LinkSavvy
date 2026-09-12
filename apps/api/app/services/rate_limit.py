"""IP + email login/registration rate limiting with exponential backoff.

Backed by the `login_attempts` table (MySQL is the sole datastore; no
Redis — see CLAUDE.md). Each failed attempt doubles the required
cool-down for that key, up to a cap.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ApiError, ErrorCode
from app.models.login_attempt import LoginAttempt

_WINDOW = timedelta(minutes=15)
_BASE_BACKOFF_SECONDS = 2
_MAX_BACKOFF_SECONDS = 300


async def _recent_failures(
    db: AsyncSession, *, email_normalized: str | None, ip_hash: str | None
) -> list[LoginAttempt]:
    since = datetime.now(UTC) - _WINDOW
    stmt = select(LoginAttempt).where(
        LoginAttempt.attempted_at >= since, LoginAttempt.succeeded.is_(False)
    )
    if email_normalized is not None:
        stmt = stmt.where(LoginAttempt.email_normalized == email_normalized)
    elif ip_hash is not None:
        stmt = stmt.where(LoginAttempt.ip_hash == ip_hash)
    result = await db.execute(stmt.order_by(LoginAttempt.attempted_at.desc()))
    return list(result.scalars().all())


async def check_rate_limit(
    db: AsyncSession,
    *,
    email_normalized: str | None,
    ip_hash: str | None,
    limit: int,
) -> None:
    for key_email, key_ip in ((email_normalized, None), (None, ip_hash)):
        if key_email is None and key_ip is None:
            continue
        failures = await _recent_failures(db, email_normalized=key_email, ip_hash=key_ip)
        if len(failures) < limit:
            continue
        last = failures[0]
        backoff = min(
            _BASE_BACKOFF_SECONDS * (2 ** (len(failures) - limit)),
            _MAX_BACKOFF_SECONDS,
        )
        retry_at = last.attempted_at + timedelta(seconds=backoff)
        now = datetime.now(UTC)
        if now < retry_at:
            raise ApiError(
                ErrorCode.RATE_LIMITED,
                "Too many attempts. Please try again later.",
                details={"retry_after_seconds": int((retry_at - now).total_seconds())},
            )


async def record_attempt(
    db: AsyncSession,
    *,
    email_normalized: str | None,
    ip_hash: str | None,
    succeeded: bool,
) -> None:
    db.add(
        LoginAttempt(
            email_normalized=email_normalized,
            ip_hash=ip_hash,
            succeeded=succeeded,
            attempted_at=datetime.now(UTC),
        )
    )
    await db.flush()
