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
    return {"email": email, "password": "secret", "id": data["user"]["id"], "first_name": data["user"]["first_name"], "last_name": data["user"]["last_name"]}

@pytest.fixture
@pytest.mark.anyio
async def user_2(client):
    resp = await client.post("/users/", json={
    "first_name": "Sohail",
    "last_name": "Amjad",
    "email": "sohail@example.com",
    "password": "secret"
})
    data = resp.json()
    email =  data["user"]["email"]
    return {"email": email, "password": "secret", "id": data["user"]["id"], "first_name": data["user"]["first_name"], "last_name": data["user"]["last_name"]}

@pytest.fixture
@pytest.mark.anyio
async def coin(client, access_token):
    response = await client.post(
        "/coins/",
        json = {
            "name": "Bitcoin",
            "symbol": "BTC",
            "price_per_unit": 123
        },
        headers = {
            "access_token": access_token
        }
    )
    id = response.json()['id']
    name = response.json()['name']
    symbol = response.json()['symbol']
    price_per_unit = response.json()['price_per_unit']
    return {"id": id, "name": name, "symbol": symbol, "price_per_unit": price_per_unit}

@pytest.fixture
@pytest.mark.anyio
async def coin_2(client, access_token):
    response = await client.post(
        "/coins/",
        json = {
            "name": "Solana",
            "symbol": "SLN",
            "price_per_unit": 100
        },
        headers = {
            "access_token": access_token
        }
    )
    id = response.json()['id']
    name = response.json()['name']
    symbol = response.json()['symbol']
    price_per_unit = response.json()['price_per_unit']
    return {"id": id, "name": name, "symbol": symbol, "price_per_unit": price_per_unit}
    
@pytest.fixture
@pytest.mark.anyio
async def deposit(client, access_token, user, coin, coin_2):
    response = await client.post(
        f"/deposit/?user_id={user.get('id')}&coin_id={coin.get('id')}&amount=120",
        headers = {"access_token": access_token}
        )
    amount = response.json()['amount']
    user_id = response.json()['user_id']
    type = response.json()["type"] == "Deposit"
    coin_id = response.json()["coin_id"]
    return {"amount": amount, "user_id": user_id, "type": type, "coin_id": coin_id, "price_per_unit": coin.get("price_per_unit")}

@pytest.fixture
@pytest.mark.anyio
async def stock(client, access_token, deposit):
    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount')-10}&price_per_unit={deposit.get('price_per_unit')}",
        headers = {"access_token": access_token}
        )
    id = response.json()['id']
    trade_type = response.json()['trade_type']
    coin_id = response.json()['coin_id']
    quantity = response.json()['quantity']
    price = response.json()['price']
    return {"id": id, "coin_id": coin_id, "trade_type": trade_type, "quantity": quantity, "price": price}