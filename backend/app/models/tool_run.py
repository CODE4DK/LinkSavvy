"""One row per tool execution -- the run endpoint's persistence layer
(see app/routers/tools.py). `context_keys` records exactly which
ContextKey values app/tools/context.py's `assemble()` included, so an
output can always be traced back to what it saw. `parent_run_id` links
a regeneration (POST /api/v1/tools/runs/{id}/regenerate) back to the
run it refined -- a chain of these is a tool's own edit history.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

ToolRunStatus = Enum("succeeded", "failed", name="tool_run_status")
ToolRunRating = Enum("up", "down", name="tool_run_rating")


class ToolRun(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tool_runs"
    __table_args__ = (
        Index("ix_tool_runs_user_tool_created", "user_id", "tool_id", "created_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # No FK -- the tool registry is code, not a table (see app/tools/registry.py).
    tool_id: Mapped[str] = mapped_column(String(96), nullable=False)
    prompt_id: Mapped[str] = mapped_column(String(96), nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    context_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    ai_invocation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("ai_invocations.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(ToolRunStatus, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[str | None] = mapped_column(ToolRunRating, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("tool_runs.id", ondelete="SET NULL"), nullable=True
    )
