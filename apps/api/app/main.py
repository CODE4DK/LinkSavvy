from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.prompts.loader import get_registry
from app.audit import job_handler  # noqa: F401 -- registers the "audit" job handler
from app.content import (  # noqa: F401 -- registers the "content_reminder" job handler
    calendar_reminder_job,
)
from app.errors import ApiError, api_error_handler
from app.growth import (
    weekly_plan_job,  # noqa: F401 -- registers the "weekly_plan.generate" job handler
)
from app.routers import (
    assistant,
    auth,
    career,
    carousels,
    content_assets,
    content_plans,
    content_voice,
    growth,
    internal,
    jobs,
    me,
    profile,
    tools,
)
from app.routers.audits import audits_router, recommendations_router, scores_router
from app.routers.dashboard import router as dashboard_router
from app.routers.workspace import folders_router as asset_folders_router
from app.routers.workspace import router as workspace_router
from app.settings import settings
from app.tools.registry import get_registry as get_tool_registry

# Fails application startup loudly if any .prompt.md file is malformed,
# rather than failing the first request that happens to use it.
get_registry()
# Same discipline for tool definitions: a bad one (an unknown prompt_id,
# an output_schema that's drifted from its prompt) fails boot, not a
# request.
get_tool_registry()

app = FastAPI(title="LinkSavvy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ApiError, api_error_handler)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(profile.router)
app.include_router(internal.router)
app.include_router(jobs.router)
app.include_router(audits_router)
app.include_router(scores_router)
app.include_router(recommendations_router)
app.include_router(dashboard_router)
app.include_router(tools.router)
app.include_router(content_voice.router)
app.include_router(content_assets.router)
app.include_router(carousels.router)
app.include_router(content_plans.router)
app.include_router(career.router)
app.include_router(growth.router)
app.include_router(workspace_router)
app.include_router(asset_folders_router)
app.include_router(assistant.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
