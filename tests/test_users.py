# tests/test_users.py

import pytest

@pytest.mark.anyio
async def test_get_token(client):
    email = "azeem@example.com"
    password = "secret"
    await client.post("/users/", json={
    "first_name": "Azeem",
    "last_name": "Amjad",
    "email": email,
    "password": password
})
    response = await client.post(
        f"/login?email={email}&password={password}")
    assert response.json()['token']
    assert response.status_code == 200

@pytest.mark.anyio
async def test_get_users_empty_without_token(client):
    r = await client.get("/users", headers={"access_token": ""})
    assert r.status_code == 403

@pytest.mark.anyio
async def test_get_users_empty_with_token(client, access_token):
    token = access_token
    r = await client.get("/users", headers={"access_token": token})
    assert r.status_code == 200


@pytest.mark.anyio
async def test_create_and_get_user_without_token(client):
    resp = await client.post("/users/", json={
    "first_name": "Azeem",
    "last_name": "Amjad",
    "email": "azeem1@example.com",
    "password": "secret"
})
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "azeem1@example.com"
    assert "id" in data["user"]

    user_id = data["user"]["id"]
    r2 = await client.get(f"/user-details?user_id={user_id}", headers={"access_token": ""})
    # breakpoint()
    assert r2.status_code == 403


@pytest.mark.anyio
async def test_create_and_get_user_with_token(client, access_token):
    resp = await client.post("/users/", json={
    "first_name": "Azeem",
    "last_name": "Amjad",
    "email": "azeem1@example.com",
    "password": "secret"
})
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "azeem1@example.com"
    assert "id" in data["user"]

    user_id = data["user"]["id"]
    r2 = await client.get(f"/user-details?user_id={user_id}", headers={"access_token": access_token})
    # breakpoint()
    assert r2.status_code == 200
