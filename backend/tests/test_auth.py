async def test_register(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@test.com",
            "password": "password123",
            "display_name": "Alice",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["email"] == "alice@test.com"
    assert "password" not in body["user"]


async def test_register_duplicate_email(client):
    payload = {
        "email": "bob@test.com",
        "password": "password123",
        "display_name": "Bob",
    }
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 409


async def test_register_short_password(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "c@test.com", "password": "short", "display_name": "C"},
    )
    assert resp.status_code == 422


async def test_login_success(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "d@test.com", "password": "password123", "display_name": "D"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "d@test.com", "password": "password123"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "e@test.com", "password": "password123", "display_name": "E"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "e@test.com", "password": "wrongpass1"}
    )
    assert resp.status_code == 401


async def test_me(client, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Test User"


async def test_me_no_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_bad_token(client):
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer garbage"}
    )
    assert resp.status_code == 401


async def test_families_requires_auth(client):
    assert (await client.get("/api/v1/families")).status_code == 401
    assert (
        await client.post("/api/v1/families", json={"name": "X"})
    ).status_code == 401
