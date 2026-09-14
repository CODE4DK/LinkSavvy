from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.profiles.schema import ProfileSnapshot


class SnapshotSummary(BaseModel):
    """One row of `GET /api/v1/profile/snapshots` — no payload, just enough
    to list and pick a version."""

    model_config = ConfigDict(from_attributes=True)

    version: int
    source: str
    captured_at: datetime
    completeness_score: int | None
    is_active: bool


class SnapshotDetail(SnapshotSummary):
    payload: ProfileSnapshot


class SyncResponse(BaseModel):
    draft: ProfileSnapshot
    available_fields: list[str]


class ImportPasteRequest(BaseModel):
    text: str


class ImportResponse(BaseModel):
    import_id: str
    status: str
    draft: ProfileSnapshot | None = None
    parse_warnings: list[str] = []
    error: str | None = None


class CommitImportRequest(BaseModel):
    payload: ProfileSnapshot


class FieldChange(BaseModel):
    path: str
    before: object | None
    after: object | None


class ListItemChange(BaseModel):
    key: str
    change: str  # 'added' | 'removed' | 'modified'
    before: dict[str, object] | None = None
    after: dict[str, object] | None = None
    field_changes: list[FieldChange] = []


class SnapshotDiff(BaseModel):
    from_version: int
    to_version: int
    field_changes: list[FieldChange]
    list_changes: dict[str, list[ListItemChange]]
