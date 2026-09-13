from __future__ import annotations

from httpx import AsyncClient

SAMPLE_RESUME_TEXT = """\
Jamie Rivera
jamie.rivera@example.com

Experience
Senior Backend Engineer, Acme Corp
Jan 2020 - Present
- Led a team of eight engineers

Skills
Python, SQL
"""

SAMPLE_JD_TEXT = """\
Senior Backend Engineer

Requirements
- 5+ years of backend engineering experience
- Strong experience with Python
"""


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    login = await client.post("/api/v1/auth/login", json=creds)
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_career_endpoints_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/career/resumes")
    assert response.status_code == 401


async def test_paste_resume_returns_a_draft_without_committing(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post(
        "/api/v1/career/resumes/parse/paste", headers=headers, json={"text": SAMPLE_RESUME_TEXT}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["draft"]["contact"]["full_name"] == "Jamie Rivera"
    assert len(body["draft"]["experiences"]) == 1

    listed = await client.get("/api/v1/career/resumes", headers=headers)
    assert listed.json() == []  # parsing never commits


async def test_commit_list_activate_and_delete_resume(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    draft = (
        await client.post(
            "/api/v1/career/resumes/parse/paste",
            headers=headers,
            json={"text": SAMPLE_RESUME_TEXT},
        )
    ).json()["draft"]

    committed = await client.post(
        "/api/v1/career/resumes",
        headers=headers,
        json={"title": "My Resume", "source": "upload", "document": draft},
    )
    assert committed.status_code == 200
    resume_id = committed.json()["id"]
    assert committed.json()["is_active"] is True
    assert committed.json()["version"] == 1

    listed = await client.get("/api/v1/career/resumes", headers=headers)
    assert len(listed.json()) == 1

    fetched = await client.get(f"/api/v1/career/resumes/{resume_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "My Resume"

    # Committing a second version deactivates the first.
    second = await client.post(
        "/api/v1/career/resumes",
        headers=headers,
        json={"title": "My Resume v2", "source": "upload", "document": draft},
    )
    assert second.json()["version"] == 2
    first_after = await client.get(f"/api/v1/career/resumes/{resume_id}", headers=headers)
    assert first_after.json()["is_active"] is False

    reactivated = await client.post(f"/api/v1/career/resumes/{resume_id}/activate", headers=headers)
    assert reactivated.json()["is_active"] is True

    deleted = await client.delete(f"/api/v1/career/resumes/{resume_id}", headers=headers)
    assert deleted.status_code == 204
    after_delete = await client.get("/api/v1/career/resumes", headers=headers)
    assert len(after_delete.json()) == 1  # only the still-undeleted v2 remains


async def test_create_list_and_delete_job_description(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post(
        "/api/v1/career/job-descriptions",
        headers=headers,
        json={
            "title": "Senior Backend Engineer",
            "company": "Acme Corp",
            "raw_text": SAMPLE_JD_TEXT,
        },
    )
    assert created.status_code == 200
    jd_id = created.json()["id"]
    assert "python" in created.json()["parsed"]["keywords"]

    listed = await client.get("/api/v1/career/job-descriptions", headers=headers)
    assert len(listed.json()) == 1

    fetched = await client.get(f"/api/v1/career/job-descriptions/{jd_id}", headers=headers)
    assert fetched.status_code == 200

    deleted = await client.delete(f"/api/v1/career/job-descriptions/{jd_id}", headers=headers)
    assert deleted.status_code == 204
    after_delete = await client.get("/api/v1/career/job-descriptions", headers=headers)
    assert after_delete.json() == []


async def test_resume_from_profile_requires_a_snapshot(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.post("/api/v1/career/resumes/from-profile", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


async def _register_and_verify(
    client: AsyncClient, sent_emails: list[dict[str, str]], *, email: str, password: str
) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Tester"}
    )
    token = next(e["token"] for e in sent_emails if e["kind"] == "verify" and e["to"] == email)
    await client.post("/api/v1/auth/verify-email", json={"token": token})
    return {"email": email, "password": password}


async def test_getting_someone_elses_resume_is_not_found(
    client: AsyncClient, sent_emails: list[dict[str, str]]
) -> None:
    creds_a = await _register_and_verify(
        client, sent_emails, email="career-a@example.com", password="correct-horse-99"
    )
    creds_b = await _register_and_verify(
        client, sent_emails, email="career-b@example.com", password="correct-horse-98"
    )
    headers_a = await _auth_headers(client, creds_a)
    headers_b = await _auth_headers(client, creds_b)

    draft = (
        await client.post(
            "/api/v1/career/resumes/parse/paste",
            headers=headers_a,
            json={"text": SAMPLE_RESUME_TEXT},
        )
    ).json()["draft"]
    committed = await client.post(
        "/api/v1/career/resumes",
        headers=headers_a,
        json={"title": "A's resume", "source": "upload", "document": draft},
    )
    resume_id = committed.json()["id"]

    forbidden = await client.get(f"/api/v1/career/resumes/{resume_id}", headers=headers_b)
    assert forbidden.status_code == 404
