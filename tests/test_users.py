# tests/test_users.py

import pytest

@pytest.mark.anyio
async def test_get_users_empty(client):
    # Expect empty list if no users in test DB
    r = await client.get("/users")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.anyio
async def test_create_and_get_user(client):
    # Create a new user
    resp = await client.post("/users/", json={
    "first_name": "Azeem",
    "last_name": "Amjad",
    "email": "azeem@example.com",
    "password": "secret"
})
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["email"] == "azeem@example.com"
    assert "id" in data["user"]

    # Retrieve created user
    user_id = data["user"]["id"]
    r2 = await client.get(f"/user-details?user_id={user_id}")
    assert r2.status_code == 200
    print(r2.json())
    u = r2.json()
    assert u["first_name"] == "Azeem"
    assert u["id"] == user_id
