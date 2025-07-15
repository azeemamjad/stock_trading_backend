import pytest

@pytest.fixture
@pytest.mark.anyio
async def access_token(client):
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
    
    return response.json()['token']