async def _create_family(client, headers, name="Test Family"):
    resp = await client.post(
        "/api/v1/families", json={"name": name}, headers=headers
    )
    return resp.json()


async def test_create_album(client, auth_headers):
    family = await _create_family(client, auth_headers)
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums",
        json={"name": "Vacation 2025", "visibility": "family"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["family_id"] == family["id"]
    assert body["name"] == "Vacation 2025"
    assert body["visibility"] == "family"


async def test_create_album_default_visibility(client, auth_headers):
    family = await _create_family(client, auth_headers)
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums",
        json={"name": "Kids"},
        headers=auth_headers,
    )
    assert resp.json()["visibility"] == "private"


async def test_create_album_invalid_visibility(client, auth_headers):
    family = await _create_family(client, auth_headers)
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums",
        json={"name": "X", "visibility": "everyone"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_album_requires_membership(client, auth_headers):
    family = await _create_family(client, auth_headers)

    import uuid

    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"o-{uuid.uuid4().hex[:8]}@t.com",
            "password": "password123",
            "display_name": "Other",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    resp = await client.post(
        f"/api/v1/families/{family['id']}/albums",
        json={"name": "X"},
        headers=other_headers,
    )
    assert resp.status_code == 403


async def test_list_albums(client, auth_headers):
    family = await _create_family(client, auth_headers)
    await client.post(
        f"/api/v1/families/{family['id']}/albums", json={"name": "A"}, headers=auth_headers
    )
    await client.post(
        f"/api/v1/families/{family['id']}/albums", json={"name": "B"}, headers=auth_headers
    )
    resp = await client.get(
        f"/api/v1/families/{family['id']}/albums", headers=auth_headers
    )
    assert [a["name"] for a in resp.json()] == ["A", "B"]


async def test_update_album(client, auth_headers):
    family = await _create_family(client, auth_headers)
    album = (
        await client.post(
            f"/api/v1/families/{family['id']}/albums",
            json={"name": "Old"},
            headers=auth_headers,
        )
    ).json()
    resp = await client.patch(
        f"/api/v1/families/{family['id']}/albums/{album['id']}",
        json={"name": "New", "visibility": "public"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"
    assert resp.json()["visibility"] == "public"


async def test_album_not_found_wrong_family(client, auth_headers):
    family = await _create_family(client, auth_headers, "F1")
    other = await _create_family(client, auth_headers, "F2")
    album = (
        await client.post(
            f"/api/v1/families/{family['id']}/albums",
            json={"name": "A"},
            headers=auth_headers,
        )
    ).json()
    resp = await client.get(
        f"/api/v1/families/{other['id']}/albums/{album['id']}", headers=auth_headers
    )
    assert resp.status_code == 404  # album belongs to 'family', not 'other'


async def test_delete_album(client, auth_headers):
    family = await _create_family(client, auth_headers)
    album = (
        await client.post(
            f"/api/v1/families/{family['id']}/albums",
            json={"name": "A"},
            headers=auth_headers,
        )
    ).json()
    resp = await client.delete(
        f"/api/v1/families/{family['id']}/albums/{album['id']}", headers=auth_headers
    )
    assert resp.status_code == 204


async def test_delete_family_cascades_albums(client, auth_headers):
    family = await _create_family(client, auth_headers)
    await client.post(
        f"/api/v1/families/{family['id']}/albums",
        json={"name": "A"},
        headers=auth_headers,
    )
    await client.delete(f"/api/v1/families/{family['id']}", headers=auth_headers)
    # family gone -> 404 before album lookup
    resp = await client.get(
        f"/api/v1/families/{family['id']}/albums", headers=auth_headers
    )
    assert resp.status_code == 404
