"""One row per gateway `run()` call — the metering ledger everything else
(cost dashboards, quota history, invalid-output rate) is computed from.
Never stores a prompt body or user content; see app/ai/redact.py."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

AIInvocationOutcome = Enum(
    "ok",
    "invalid_output",
    "provider_error",
    "quota_denied",
    "policy_blocked",
    name="ai_invocation_outcome",
)


class AIInvocation(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_invocations"
    __table_args__ = (
        Index("ix_ai_invocations_user_created", "user_id", "created_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    prompt_id: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    tier: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fallback_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outcome: Mapped[str] = mapped_column(AIInvocationOutcome, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
