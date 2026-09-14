from __future__ import annotations

from httpx import AsyncClient


async def _access_token(client: AsyncClient, creds: dict[str, str]) -> str:
    login = await client.post("/api/v1/auth/login", json=creds)
    return str(login.json()["access_token"])


async def _auth_headers(client: AsyncClient, creds: dict[str, str]) -> dict[str, str]:
    token = await _access_token(client, creds)
    return {"Authorization": f"Bearer {token}"}


SAMPLE_PAYLOAD = {
    "title": "My carousel",
    "data": {
        "template": "clean",
        "cover": {"headline": "Cover headline", "subhead": "Cover subhead"},
        "slides": [
            {"headline": "Slide one", "body": "Body one", "visual_note": "note"},
            {"headline": "Slide two", "body": "Body two", "visual_note": "note"},
        ],
        "closing": {"cta": "Closing CTA"},
        "caption": "A caption",
    },
}


async def test_create_carousel_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/carousels", json=SAMPLE_PAYLOAD)
    assert response.status_code == 401


async def test_create_get_and_update_carousel(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)

    created = await client.post("/api/v1/carousels", headers=headers, json=SAMPLE_PAYLOAD)
    assert created.status_code == 200
    carousel_id = created.json()["id"]
    assert len(created.json()["data"]["slides"]) == 2

    fetched = await client.get(f"/api/v1/carousels/{carousel_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "My carousel"

    updated_payload = {**SAMPLE_PAYLOAD, "title": "Updated title"}
    updated = await client.put(
        f"/api/v1/carousels/{carousel_id}", headers=headers, json=updated_payload
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated title"


async def test_export_pdf_returns_a_pdf_file(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post("/api/v1/carousels", headers=headers, json=SAMPLE_PAYLOAD)
    carousel_id = created.json()["id"]

    response = await client.post(f"/api/v1/carousels/{carousel_id}/export/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


async def test_export_png_returns_a_zip_file(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    created = await client.post("/api/v1/carousels", headers=headers, json=SAMPLE_PAYLOAD)
    carousel_id = created.json()["id"]

    response = await client.post(f"/api/v1/carousels/{carousel_id}/export/png", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.content.startswith(b"PK")


async def test_get_carousel_404s_for_unknown_id(
    client: AsyncClient, registered_user: dict[str, str]
) -> None:
    headers = await _auth_headers(client, registered_user)
    response = await client.get(
        "/api/v1/carousels/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
