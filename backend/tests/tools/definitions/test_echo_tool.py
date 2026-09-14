"""test.echo is the Tool Framework's own proof: nothing here adds a new
router, service function, or frontend component -- these tests exercise
it through the exact same `GET /api/v1/tools`, `POST .../run`, and
`POST .../save` endpoints every real Profile Hub tool uses, plus the
admin+flag visibility gate that hides any `test.*` tool from everyone
else (mirroring app/routers/internal.py's developer playground).
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feature_flag import FeatureFlag
from app.models.user import User


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _promote_to_admin(db: AsyncSession, email: str) -> None:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one()
    user.role = "admin"
    await db.commit()


async def _set_playground_flag(db: AsyncSession, *, enabled: bool) -> None:
    flag = (
        await db.execute(select(FeatureFlag).where(FeatureFlag.key == "dev.playground"))
    ).scalar_one()
    flag.enabled_globally = enabled
    await db.commit()


async def test_echo_is_hidden_from_a_normal_user(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.get("/api/v1/tools", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "test.echo" not in {tool["id"] for tool in response.json()}


async def test_echo_run_is_a_404_for_a_normal_user(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    token = await _access_token(client, registered_user)
    response = await client.post(
        "/api/v1/tools/test.echo/run",
        json={"input": {"user_supplied_text": "hi"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


async def test_echo_is_hidden_from_an_admin_without_the_flag(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    await _promote_to_admin(db_session, registered_user["email"])
    await _set_playground_flag(db_session, enabled=False)
    token = await _access_token(client, registered_user)
    response = await client.get("/api/v1/tools", headers={"Authorization": f"Bearer {token}"})
    assert "test.echo" not in {tool["id"] for tool in response.json()}


async def test_echo_appears_and_runs_and_saves_for_an_admin_with_the_flag(
    client: AsyncClient, db_session: AsyncSession, registered_user: dict[str, str]
) -> None:
    await _promote_to_admin(db_session, registered_user["email"])
    token = await _access_token(client, registered_user)
    headers = {"Authorization": f"Bearer {token}"}

    list_response = await client.get("/api/v1/tools", headers=headers)
    tools_by_id = {tool["id"]: tool for tool in list_response.json()}
    assert "test.echo" in tools_by_id
    echo_tool = tools_by_id["test.echo"]
    assert echo_tool["input_schema"]["properties"]["user_supplied_text"]["type"] == "string"
    assert echo_tool["result_renderer"] == "document"

    run_response = await client.post(
        "/api/v1/tools/test.echo/run",
        json={"input": {"user_supplied_text": "hello from the tool framework"}},
        headers=headers,
    )
    assert run_response.status_code == 200
    body = run_response.json()
    assert body["output"]["sections"][0]["body"] == "hello from the tool framework"

    save_response = await client.post(
        f"/api/v1/tools/runs/{body['run_id']}/save",
        json={"title": "Echo test", "body": body["output"]["sections"][0]["body"]},
        headers=headers,
    )
    assert save_response.status_code == 200
    assert save_response.json()["type"] == "template"
