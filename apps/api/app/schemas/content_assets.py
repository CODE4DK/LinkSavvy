from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.tools.definition import AssetType


class CreateAssetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: AssetType = AssetType.POST
    title: str
    body: str
    folder_id: uuid.UUID | None = None


class MarkPostedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    linkedin_url: str | None = None
