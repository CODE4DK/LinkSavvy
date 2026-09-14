from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    status: str
    attempts: int
    max_attempts: int
    progress_percent: int
    error: str | None
    result: dict[str, Any] | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
