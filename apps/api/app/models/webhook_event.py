"""Every inbound provider webhook, persisted before it is processed.

`provider_event_id` is unique so a replayed delivery (providers retry
until they see a 2xx) can never be applied twice -- see
app/billing/service.py::process_webhook_event, which inserts this row
*first* and only then runs the normalised handling, keyed on whether a
row for that id already existed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Enum, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db_types import UTCDateTime
from app.models.base import Base, PrimaryKeyMixin, TimestampMixin

WebhookEventProvider = Enum("stripe", "razorpay", name="webhook_event_provider")
WebhookEventStatus = Enum("pending", "processed", "failed", name="webhook_event_status")


class WebhookEvent(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_webhook_events_provider_event"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    provider: Mapped[str] = mapped_column(WebhookEventProvider, nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    status: Mapped[str] = mapped_column(WebhookEventStatus, nullable=False, default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
