from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.errors import ApiError, api_error_handler
from app.routers import auth, me, profile
from app.settings import settings

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
