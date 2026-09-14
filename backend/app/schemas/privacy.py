from __future__ import annotations

from pydantic import BaseModel


class ExportJobResponse(BaseModel):
    job_id: str
