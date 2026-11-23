import uuid


async def _register(client, name="User"):
    email = f"{name.lower()}-{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": name},
    )
    return {"email": email, "headers": {"Authorization": f"Bearer {resp.json()['access_token']}"}}


async def _create_family(client, headers, name="Family"):
    return (
        await client.post("/api/v1/families", json={"name": name}, headers=headers)
    ).json()


async def test_invite_and_accept_flow(client):
    owner = await _register(client, "Owner")
    invitee = await _register(client, "Invitee")
    family = await _create_family(client, owner["headers"])

    resp = await client.post(
        f"/api/v1/families/{family['id']}/invitations",
        json={"email": invitee["email"], "role": "member"},
        headers=owner["headers"],
    )
    assert resp.status_code == 201
    token = resp.json()["token"]

    # invitee sees it in /invitations/mine
    mine = await client.get("/api/v1/invitations/mine", headers=invitee["headers"])
    assert any(i["token"] == token for i in mine.json())

    # invitee accepts
    resp = await client.post(
        f"/api/v1/invitations/{token}/accept", headers=invitee["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["accepted_at"] is not None

    # invitee can now see the family
    fams = await client.get("/api/v1/families", headers=invitee["headers"])
    assert family["id"] in [f["id"] for f in fams.json()]

    # token cannot be reused
    resp = await client.post(
        f"/api/v1/invitations/{token}/accept", headers=invitee["headers"]
    )
    assert resp.status_code == 409


async def test_invite_wrong_email_cannot_accept(client):
    owner = await _register(client, "Owner")
    other = await _register(client, "Other")
    family = await _create_family(client, owner["headers"])

    token = (
        await client.post(
            f"/api/v1/families/{family['id']}/invitations",
            json={"email": "someone-else@test.com", "role": "member"},
            headers=owner["headers"],
        )
    ).json()["token"]

    # a different registered user tries to accept
    resp = await client.post(
        f"/api/v1/invitations/{token}/accept", headers=other["headers"]
    )
    assert resp.status_code == 403


async def test_member_cannot_invite(client):
    owner = await _register(client, "Owner")
    member = await _register(client, "Member")
    family = await _create_family(client, owner["headers"])

    token = (
        await client.post(
            f"/api/v1/families/{family['id']}/invitations",
            json={"email": member["email"], "role": "member"},
            headers=owner["headers"],
        )
    ).json()["token"]
    await client.post(f"/api/v1/invitations/{token}/accept", headers=member["headers"])

    resp = await client.post(
        f"/api/v1/families/{family['id']}/invitations",
        json={"email": "x@test.com", "role": "member"},
        headers=member["headers"],
    )
    assert resp.status_code == 403


async def test_non_member_cannot_invite(client):
    owner = await _register(client, "Owner")
    stranger = await _register(client, "Stranger")
    family = await _create_family(client, owner["headers"])

    resp = await client.post(
        f"/api/v1/families/{family['id']}/invitations",
        json={"email": "x@test.com", "role": "member"},
        headers=stranger["headers"],
    )
    assert resp.status_code == 403


async def test_invite_existing_member_rejected(client):
    owner = await _register(client, "Owner")
    family = await _create_family(client, owner["headers"])
    resp = await client.post(
        f"/api/v1/families/{family['id']}/invitations",
        json={"email": owner["email"], "role": "member"},
        headers=owner["headers"],
    )
    assert resp.status_code == 409


async def test_list_members(client):
    owner = await _register(client, "Owner")
    family = await _create_family(client, owner["headers"])
    members = (
        await client.get(f"/api/v1/families/{family['id']}/members", headers=owner["headers"])
    ).json()
    assert len(members) == 1
    assert members[0]["user"]["email"] == owner["email"]
    assert members[0]["role"] == "owner"


async def test_admin_can_invite_member_cannot_manage(client):
    owner = await _register(client, "Owner")
    admin = await _register(client, "Admin")
    family = await _create_family(client, owner["headers"])

    token = (
        await client.post(
            f"/api/v1/families/{family['id']}/invitations",
            json={"email": admin["email"], "role": "admin"},
            headers=owner["headers"],
        )
    ).json()["token"]
    await client.post(f"/api/v1/invitations/{token}/accept", headers=admin["headers"])

    # admin can invite
    resp = await client.post(
        f"/api/v1/families/{family['id']}/invitations",
        json={"email": "new@test.com", "role": "member"},
        headers=admin["headers"],
    )
    assert resp.status_code == 201

    # but cannot delete the family (owner/admin can — admin CAN)
    resp = await client.delete(f"/api/v1/families/{family['id']}", headers=admin["headers"])
    assert resp.status_code == 204
