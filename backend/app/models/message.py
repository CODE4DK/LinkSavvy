"""One turn in a Conversation. `parent_message_id` is what makes editing
a user message branch rather than destroy history: editing message N
creates a new message N' with `parent_message_id` pointing at N's own
parent (not at N), so both N and N' are siblings under the same parent
and the conversation can show both branches and let the user switch (see
app/assistant/service.py's `edit_and_branch`). `tool_call` is a small,
shape-varying JSON side-channel for whichever structured thing this
message represents beyond its plain text: an orchestrator tool proposal
(`{tool_id, reasoning, prefilled_input}`), the absorbed Growth Coach's
phase/score_movement metadata, or a `role="tool"` message's read-only
assistant-tool call and result (see docs/adr/0010 for why read calls are
recorded here rather than in `ai_invocations`, which is specifically the
gateway's own metering ledger)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

MessageRole = Enum("user", "assistant", "system", "tool", name="message_role")

# MEDIUMTEXT on MySQL, mirroring app.models.asset's _LongText -- a long
# conversation turn (a pasted résumé, a long tool proposal) can exceed
# TEXT's 64KB. Plain TEXT on SQLite, the test suite's only dialect.
_LongText = Text().with_variant(mysql.MEDIUMTEXT(), "mysql")


class Message(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(MessageRole, nullable=False)
    content: Mapped[str] = mapped_column(_LongText, nullable=False)
    tool_call: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    tool_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("tool_runs.id", ondelete="SET NULL"), nullable=True
    )
    ai_invocation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("ai_invocations.id", ondelete="SET NULL"), nullable=True
    )
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
