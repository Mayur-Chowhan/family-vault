async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_create_family(client, auth_headers):
    resp = await client.post(
        "/api/v1/families", json={"name": "Sharma Family"}, headers=auth_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == 1
    assert body["name"] == "Sharma Family"
    assert "created_at" in body


async def test_create_family_validation(client, auth_headers):
    resp = await client.post(
        "/api/v1/families", json={"name": ""}, headers=auth_headers
    )
    assert resp.status_code == 422


async def test_list_families(client, auth_headers):
    await client.post("/api/v1/families", json={"name": "A"}, headers=auth_headers)
    await client.post("/api/v1/families", json={"name": "B"}, headers=auth_headers)
    resp = await client.get("/api/v1/families", headers=auth_headers)
    assert resp.status_code == 200
    assert [f["name"] for f in resp.json()] == ["A", "B"]


async def test_list_families_only_own(client, auth_headers):
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
    await client.post("/api/v1/families", json={"name": "Mine"}, headers=auth_headers)
    await client.post("/api/v1/families", json={"name": "Theirs"}, headers=other_headers)

    resp = await client.get("/api/v1/families", headers=auth_headers)
    assert [f["name"] for f in resp.json()] == ["Mine"]


async def test_get_family(client, auth_headers):
    created = (
        await client.post("/api/v1/families", json={"name": "A"}, headers=auth_headers)
    ).json()
    resp = await client.get(f"/api/v1/families/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "A"


async def test_get_family_not_found(client, auth_headers):
    resp = await client.get("/api/v1/families/999", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_family_forbidden_for_non_member(client, auth_headers):
    created = (
        await client.post("/api/v1/families", json={"name": "A"}, headers=auth_headers)
    ).json()

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
    resp = await client.get(
        f"/api/v1/families/{created['id']}", headers=other_headers
    )
    assert resp.status_code == 403


async def test_update_family(client, auth_headers):
    created = (
        await client.post("/api/v1/families", json={"name": "Old"}, headers=auth_headers)
    ).json()
    resp = await client.patch(
        f"/api/v1/families/{created['id']}", json={"name": "New"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


async def test_delete_family(client, auth_headers):
    created = (
        await client.post("/api/v1/families", json={"name": "A"}, headers=auth_headers)
    ).json()
    resp = await client.delete(
        f"/api/v1/families/{created['id']}", headers=auth_headers
    )
    assert resp.status_code == 204
    assert (
        await client.get(f"/api/v1/families/{created['id']}", headers=auth_headers)
    ).status_code == 404


async def test_creator_is_owner(client, auth_headers):
    family = (
        await client.post("/api/v1/families", json={"name": "A"}, headers=auth_headers)
    ).json()
    members = (
        await client.get(f"/api/v1/families/{family['id']}/members", headers=auth_headers)
    ).json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"
