from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

BulkAction = Literal["move", "tag", "delete", "export"]


class WorkspaceAssetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    title: str
    body: str
    body_format: str
    metadata: dict[str, Any]
    source_tool_run_id: str | None
    tags: list[str]
    is_favourite: bool
    folder_id: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class AssetListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[WorkspaceAssetResponse]
    next_cursor: str | None


class AssetPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
    folder_id: str | None = Field(default=None)
    unfile: bool = False
    is_favourite: bool | None = None


class AssetVersionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    title: str
    body: str
    body_format: str
    created_at: datetime


class BulkActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: BulkAction
    asset_ids: list[str] = Field(min_length=1, max_length=200)
    folder_id: str | None = None
    tags: list[str] | None = None
    format: Literal["txt", "md", "pdf", "docx"] = "txt"


class BulkActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    affected_count: int


class AssetFolderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    parent_id: str | None


class AssetFolderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    parent_id: str | None = None


class AssetFolderUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    parent_id: str | None = None
    unfile: bool = False
