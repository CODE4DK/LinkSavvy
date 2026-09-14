"""Response cache keyed by sha256(prompt_id, version, context, tier,
model) — see app/ai/gateway.py step 3. Storing the response here (not
just a hit/miss flag) means a cache hit costs one row read and zero
provider calls."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class AICache(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_cache"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    cache_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    prompt_id: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    response: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
