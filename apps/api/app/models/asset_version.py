"""A prior state of an `Asset` edited in place. Written just before an
in-place edit overwrites `Asset.title`/`body`/`body_format`/`metadata_`,
so `asset_versions` holds what the asset looked like *before* each edit
-- version 1 is the asset's original state, version N is what it looked
like just before its Nth edit. Append-only, no `updated_at`.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UTCDateTime, UUIDBinary
from app.models.base import Base, PrimaryKeyMixin

_LongText = Text().with_variant(mysql.MEDIUMTEXT(), "mysql")


class AssetVersion(PrimaryKeyMixin, Base):
    __tablename__ = "asset_versions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(_LongText, nullable=False)
    body_format: Mapped[str] = mapped_column(String(16), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(), server_default=func.now(), nullable=False
    )
