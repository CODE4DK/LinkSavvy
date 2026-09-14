from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin


class AuditLog(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_log"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Mapped to the `metadata` column; the attribute is renamed because
    # `metadata` is reserved by SQLAlchemy's declarative base.
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
