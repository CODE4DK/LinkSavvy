from __future__ import annotations

import json

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature_flag import FeatureFlag
from app.models.user import User


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _promote_to_admin(db: AsyncSession, email: str) -> str:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    user.role = "admin"
    await db.commit()
    return str(user.id)


async def _set_playground_flag(db: AsyncSession, *, enabled: bool) -> None:
    flag = (
        await db.execute(select(FeatureFlag).where(FeatureFlag.key == "dev.playground"))
    ).scalar_one()
    flag.enabled_globally = enabled
    await db.commit()


async def _admin_headers(
    client: AsyncClient, db: AsyncSession, registered_user: dict[str, str]
) -> dict[str, str]:
    await _promote_to_admin(db, registered_user["email"])
    token = await _access_token(client, registered_user)
    return {"Authorization": f"Bearer {token}"}


async def test_prompts_list_requires_admin(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.get(
        "/internal/playground/prompts", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


async def test_prompts_list_requires_the_flag(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _admin_headers(client, db_session, registered_user)
    await _set_playground_flag(db_session, enabled=False)
    response = await client.get("/internal/playground/prompts", headers=headers)
    assert response.status_code == 403


async def test_prompts_list_returns_seed_prompts(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _admin_headers(client, db_session, registered_user)
    response = await client.get("/internal/playground/prompts", headers=headers)
    assert response.status_code == 200
    ids = {p["id"] for p in response.json()}
    # The Phase 3 seed prompts must always be listed -- other phases (like
    # Phase 4's Audit Engine) register their own prompts alongside these,
    # so this checks a subset rather than an exact, ever-growing set.
    assert {"profile.headline.v1", "text.summarise.v1", "meta.classify_intent.v1"} <= ids
    headline = next(p for p in response.json() if p["id"] == "profile.headline.v1")
    assert headline["output_schema"] is not None
    assert "profile_summary" in headline["required_context"]
    text_prompt = next(p for p in response.json() if p["id"] == "text.summarise.v1")
    assert text_prompt["output_schema"] is None


async def test_run_text_prompt(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _admin_headers(client, db_session, registered_user)
    response = await client.post(
        "/internal/playground/run",
        json={"prompt_id": "text.summarise.v1", "context": {"text": "some text"}},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["parsed"] is None
    assert isinstance(body["text"], str) and body["text"]
    assert body["cached"] is False


async def test_run_schema_prompt(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _admin_headers(client, db_session, registered_user)
    response = await client.post(
        "/internal/playground/run",
        json={
            "prompt_id": "profile.headline.v1",
            "context": {"profile_summary": "engineer", "target_role": "staff engineer"},
        },
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "variants" in body["parsed"]


async def test_run_rejects_invalid_tier_override(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _admin_headers(client, db_session, registered_user)
    response = await client.post(
        "/internal/playground/run",
        json={
            "prompt_id": "text.summarise.v1",
            "context": {"text": "hi"},
            "tier_override": "not-a-real-tier",
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_run_missing_required_context_returns_422(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _admin_headers(client, db_session, registered_user)
    response = await client.post(
        "/internal/playground/run",
        json={"prompt_id": "text.summarise.v1", "context": {}},
        headers=headers,
    )
    assert response.status_code == 422


async def test_stream_returns_sse_frames(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    headers = await _admin_headers(client, db_session, registered_user)
    async with client.stream(
        "POST",
        "/internal/playground/stream",
        json={"prompt_id": "text.summarise.v1", "context": {"text": "hi"}},
        headers=headers,
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = b""
        async for chunk in response.aiter_bytes():
            body += chunk

    lines = [line for line in body.decode().split("\n\n") if line.strip()]
    frames = [json.loads(line.removeprefix("data: ")) for line in lines]
    types = [f["type"] for f in frames]
    assert types[0] == "meta"
    assert types[-1] == "done"
    assert "delta" in types
