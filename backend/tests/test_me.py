from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def test_update_profile(client: AsyncClient, registered_user: dict[str, str]) -> None:
    access_token = await _access_token(client, registered_user)
    response = await client.patch(
        "/api/v1/me",
        json={"full_name": "New Name", "timezone": "America/New_York"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "New Name"
    assert body["timezone"] == "America/New_York"


async def test_update_profile_rejects_unknown_timezone(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    access_token = await _access_token(client, registered_user)
    response = await client.patch(
        "/api/v1/me",
        json={"timezone": "Not/A_Zone"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 422


async def test_delete_account_requires_correct_password(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    access_token = await _access_token(client, registered_user)
    bad = await client.request(
        "DELETE",
        "/api/v1/me",
        json={"current_password": "wrong"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert bad.status_code == 401

    good = await client.request(
        "DELETE",
        "/api/v1/me",
        json={"current_password": registered_user["password"]},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert good.status_code == 200

    relogin = await client.post("/api/v1/auth/login", json=registered_user)
    assert relogin.status_code == 403
    assert relogin.json()["error"]["code"] == "FORBIDDEN"


async def test_request_and_download_data_export(
    client: AsyncClient,
    registered_user: dict[str, str],
    db_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    from app.jobs.worker import run_once

    access_token = await _access_token(client, registered_user)
    headers = {"Authorization": f"Bearer {access_token}"}

    requested = await client.post("/api/v1/me/export", headers=headers)
    assert requested.status_code == 200
    job_id = requested.json()["job_id"]

    processed = await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    assert processed is True

    job_status = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert job_status.status_code == 200
    assert job_status.json()["status"] == "succeeded"
    export_id = job_status.json()["result"]["export_id"]

    download = await client.get(f"/api/v1/me/export/{export_id}", headers=headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/zip"

    import io
    import zipfile

    archive = zipfile.ZipFile(io.BytesIO(download.content))
    assert "account.json" in archive.namelist()


async def test_cannot_download_someone_elses_export(
    client: AsyncClient,
    registered_user: dict[str, str],
    db_sessionmaker: async_sessionmaker[AsyncSession],
    sent_emails: list[dict[str, str]],
) -> None:
    from app.jobs.worker import run_once

    access_token = await _access_token(client, registered_user)
    headers = {"Authorization": f"Bearer {access_token}"}
    requested = await client.post("/api/v1/me/export", headers=headers)
    job_id = requested.json()["job_id"]
    await run_once(worker_id="test-worker", session_factory=db_sessionmaker)
    job_status = await client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    export_id = job_status.json()["result"]["export_id"]

    other_creds = {"email": "other-export@example.com", "password": "correct-horse-99"}
    await client.post(
        "/api/v1/auth/register",
        json={**other_creds, "full_name": "Other"},
    )
    token = next(
        e["token"] for e in sent_emails if e["kind"] == "verify" and e["to"] == other_creds["email"]
    )
    await client.post("/api/v1/auth/verify-email", json={"token": token})
    other_login = await client.post("/api/v1/auth/login", json=other_creds)
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = await client.get(f"/api/v1/me/export/{export_id}", headers=other_headers)
    assert response.status_code == 404
