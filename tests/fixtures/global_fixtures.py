import pytest

@pytest.fixture
@pytest.mark.anyio
async def access_token(client):
    email = "fixture@example.com"
    password = "secret"
    await client.post("/users/", json={
    "first_name": "Fixture",
    "last_name": "Test",
    "email": email,
    "password": password
})
    response = await client.post(
        f"/login?email={email}&password={password}")
    
    return response.json()['token']

@pytest.fixture
@pytest.mark.anyio
async def user(client):
    resp = await client.post("/users/", json={
    "first_name": "Azeem",
    "last_name": "Amjad",
    "email": "azeem@example.com",
    "password": "secret"
})
    data = resp.json()
    email =  data["user"]["email"]
    return {"email": email, "password": "secret", "id": data["user"]["id"]}