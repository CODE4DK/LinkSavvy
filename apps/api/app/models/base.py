"""Declarative base and shared mixins for all ORM models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid6 import uuid7

from app.db_types import UTCDateTime, UUIDBinary


def new_uuid7() -> uuid.UUID:
    return uuid7()


class Base(DeclarativeBase):
    pass


class PrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUIDBinary, primary_key=True, default=new_uuid7)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
