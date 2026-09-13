"""A conversation with the AI Assistant -- one row per thread shown in
the conversation list, whatever `mode` it runs in (`auto` for the general
assistant, `tool` for a conversation pinned to one tool, `coach` for the
absorbed Phase 8 Growth Coach). `context_snapshot` records the "what I can
see" panel's per-item toggle state (which context keys the user excluded)
so it's remembered across turns and across page loads, not just for the
turn that set it. `asset_id` is set once the user saves this conversation
to Workspace (see app.tools.definition.AssetType.CONVERSATION, already
defined in Phase 05)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

ConversationMode = Enum("auto", "tool", "coach", name="conversation_mode")


class Conversation(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_user_updated", "user_id", "updated_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[str] = mapped_column(ConversationMode, nullable=False, default="auto")
    context_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_message_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
