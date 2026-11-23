import io
import uuid

import pytest

import cloudinary
import cloudinary.uploader
from app.routers import media as media_router


@pytest.fixture(autouse=True)
def mock_cloudinary(monkeypatch):
    monkeypatch.setattr(media_router, "cloudinary_enabled", lambda: True)
    monkeypatch.setattr(
        cloudinary.uploader,
        "upload",
        lambda data, **kwargs: {
            "public_id": f"family_1/album_1/test_{uuid.uuid4().hex[:6]}",
            "resource_type": "image",
            "format": "jpg",
            "bytes": len(data),
            "width": 800,
            "height": 600,
        },
    )
    monkeypatch.setattr(cloudinary.uploader, "destroy", lambda *a, **k: {"result": "ok"})
    # media_url needs a cloud name to build URLs
    from types import SimpleNamespace

    monkeypatch.setattr(
        cloudinary, "config", lambda *a, **k: SimpleNamespace(cloud_name="test-cloud")
    )


async def _setup(client):
    email = f"u-{uuid.uuid4().hex[:8]}@t.com"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": "U"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    family = (
        await client.post("/api/v1/families", json={"name": "F"}, headers=headers)
    ).json()
    album = (
        await client.post(
            f"/api/v1/families/{family['id']}/albums",
            json={"name": "A"},
            headers=headers,
        )
    ).json()
    return headers, family, album


def _jpeg():
    return io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9")


async def test_upload_image(client):
    headers, family, album = await _setup(client)
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        files={"file": ("photo.jpg", _jpeg(), "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["resource_type"] == "image"
    assert body["width"] == 800
    assert "test-cloud" in body["url"]
    assert "w_400" in body["thumbnail_url"]
    assert body["original_filename"] == "photo.jpg"


async def test_upload_unsupported_type(client):
    headers, family, album = await _setup(client)
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        files={"file": ("evil.exe", b"MZ", "application/x-msdownload")},
        headers=headers,
    )
    assert resp.status_code == 415


async def test_list_media(client):
    headers, family, album = await _setup(client)
    await client.post(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
        headers=headers,
    )
    await client.post(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        files={"file": ("b.jpg", _jpeg(), "image/jpeg")},
        headers=headers,
    )
    resp = await client.get(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        headers=headers,
    )
    assert len(resp.json()["items"]) == 2
    assert resp.json()["total"] == 2


async def test_pagination(client):
    headers, family, album = await _setup(client)
    url = f"/api/v1/families/{family['id']}/albums/{album['id']}/media"
    for i in range(25):
        await client.post(
            url,
            files={"file": (f"p{i}.jpg", _jpeg(), "image/jpeg")},
            headers=headers,
        )
    page1 = (await client.get(f"{url}?page=1&page_size=20", headers=headers)).json()
    page2 = (await client.get(f"{url}?page=2&page_size=20", headers=headers)).json()
    assert len(page1["items"]) == 20
    assert len(page2["items"]) == 5
    assert page1["total"] == 25
    ids1 = {m["id"] for m in page1["items"]}
    ids2 = {m["id"] for m in page2["items"]}
    assert not ids1 & ids2


async def test_download_url_present(client):
    headers, family, album = await _setup(client)
    created = (
        await client.post(
            f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
            files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
            headers=headers,
        )
    ).json()
    assert "fl_attachment" in created["download_url"]


async def test_delete_media(client):
    headers, family, album = await _setup(client)
    created = (
        await client.post(
            f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
            files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
            headers=headers,
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media/{created['id']}",
        headers=headers,
    )
    assert resp.status_code == 204
    remaining = await client.get(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        headers=headers,
    )
    assert remaining.json()["items"] == []


async def test_media_requires_membership(client):
    headers, family, album = await _setup(client)

    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"o-{uuid.uuid4().hex[:8]}@t.com",
            "password": "password123",
            "display_name": "O",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
        headers=other_headers,
    )
    assert resp.status_code == 403


async def test_upload_without_cloudinary_config(client, monkeypatch):
    monkeypatch.setattr(media_router, "cloudinary_enabled", lambda: False)
    headers, family, album = await _setup(client)
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums/{album['id']}/media",
        files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
        headers=headers,
    )
    assert resp.status_code == 503
