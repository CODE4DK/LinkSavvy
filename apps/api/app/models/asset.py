"""A user's saved output -- a tool run they chose to keep (Save to
Workspace), organised into folders and searchable by title/body. The
FULLTEXT index is infrastructure for a later phase's Workspace search;
nothing in this phase queries it yet.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db_types import UUIDBinary
from app.models.base import Base, PrimaryKeyMixin, SoftDeleteMixin, TimestampMixin

AssetType = Enum(
    "post",
    "headline",
    "about",
    "experience_bullets",
    "comment",
    "message",
    "resume",
    "cover_letter",
    "job_description",
    "analysis",
    "conversation",
    "template",
    "carousel",
    "roadmap",
    name="asset_type",
)
AssetBodyFormat = Enum("text", "markdown", "json", name="asset_body_format")

# MEDIUMTEXT on MySQL (a saved asset's body can exceed TEXT's 64KB, e.g. a
# long-form document or a full conversation transcript); plain TEXT
# elsewhere (SQLite, used only by the test suite) since it has no
# equivalent column-size ceiling to work around.
_LongText = Text().with_variant(mysql.MEDIUMTEXT(), "mysql")


class AssetFolder(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "asset_folders"
    __table_args__ = ({"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("asset_folders.id", ondelete="SET NULL"), nullable=True
    )


class Asset(PrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_user_folder", "user_id", "folder_id"),
        Index("ft_assets_title_body", "title", "body", mysql_prefix="FULLTEXT"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDBinary, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(AssetType, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(_LongText, nullable=False)
    body_format: Mapped[str] = mapped_column(AssetBodyFormat, nullable=False, default="text")
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    # No FK -- a saved asset outlives the run that produced it (a
    # ToolRun's ai_invocation_id similarly points at metering history
    # without pinning the asset's lifetime to it).
    source_tool_run_id: Mapped[uuid.UUID | None] = mapped_column(UUIDBinary, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_favourite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDBinary, ForeignKey("asset_folders.id", ondelete="SET NULL"), nullable=True
    )
    # Set by app.billing.entitlements when a downgrade puts this asset
    # over the free plan's storage cap -- never deleted, just frozen.
    # Cleared the moment the user is pro again, regardless of which asset
    # caused the overflow at the time.
    read_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
