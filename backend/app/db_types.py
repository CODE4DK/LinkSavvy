"""Shared SQLAlchemy column types."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import BINARY, DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Always-aware UTC datetimes in Python; naive UTC in the database.

    Neither MySQL's DATETIME nor SQLite's storage keep timezone info, so a
    plain `DateTime(timezone=True)` round-trips as a naive value and blows
    up the moment it's compared against `datetime.now(UTC)`. This type
    strips tzinfo on the way in (after normalising to UTC) and reattaches
    `UTC` on the way out, so application code only ever sees aware values.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect: object) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class UUIDBinary(TypeDecorator[uuid.UUID]):
    """Stores a UUID as BINARY(16); exposes it as `uuid.UUID` in Python."""

    impl = BINARY(16)
    cache_ok = True

    def process_bind_param(self, value: object, dialect: object) -> bytes | None:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.bytes
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return uuid.UUID(value).bytes
        raise TypeError(f"Cannot bind {value!r} as a UUID")

    def process_result_value(self, value: object, dialect: object) -> uuid.UUID | None:
        if value is None:
            return None
        return uuid.UUID(bytes=value)  # type: ignore[arg-type]
