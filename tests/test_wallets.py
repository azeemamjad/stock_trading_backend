import pytest


# tests for Wallet
@pytest.mark.anyio
async def test_get_wallet(client, user, access_token):
    response = await client.get(
        f"/wallet/?user_id={user.get('id')}", headers={"access_token": access_token}
    )
    assert response.json()["name"] == user.get("first_name") + " " + user.get(
        "last_name"
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_wallet_without_token(client, user):
    response = await client.get(f"/wallet/?user_id={user.get('id')}")
    assert (
        response.json()["message"] == "You are not authenticated to use this route..."
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_wallet_without_user(client, access_token):
    response = await client.get("/wallet/", headers={"access_token": access_token})
    assert response.json()["detail"][0]["loc"][1] == "user_id"
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_wallet_with_wrong_user(client, access_token):
    response = await client.get(
        "/wallet/?user_id=7", headers={"access_token": access_token}
    )
    assert response.json()["detail"] == "User Does Not Exist!"
    assert response.status_code == 400


# tests for Coins
@pytest.mark.anyio
async def test_add_coin(client, access_token):
    response = await client.post(
        "/coins/",
        json={"name": "Bitcoin", "symbol": "BTC", "price_per_unit": 123},
        headers={"access_token": access_token},
    )
    assert response.json()["name"] == "Bitcoin"
    assert response.json()["symbol"] == "BTC"
    assert response.json()["price_per_unit"] == 123
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_coin_list(client, coin, coin_2, coin_3):
    response = await client.get("/coins/")
    assert response.json()[0]["id"] == coin.get("id")
    assert response.json()[1]["id"] == coin_2.get("id")
    assert response.json()[2]["id"] == coin_3.get("id")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_add_coin_without_token(client):
    response = await client.post(
        "/coins/", json={"name": "Bitcoin", "symbol": "BTC", "price_per_unit": 123}
    )
    assert (
        response.json()["message"] == "You are not authenticated to use this route..."
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_add_coin_without_json(client, access_token):
    response = await client.post("/coins/", headers={"access_token": access_token})
    assert response.json()["detail"][0]["loc"][0] == "body"
    assert response.status_code == 422


@pytest.mark.anyio
async def test_add_duplicate_coin(client, access_token):
    response = await client.post(
        "/coins/",
        json={"name": "Bitcoin", "symbol": "BTC", "price_per_unit": 123},
        headers={"access_token": access_token},
    )

    assert response.json()["name"] == "Bitcoin"
    assert response.json()["symbol"] == "BTC"
    assert response.json()["price_per_unit"] == 123
    assert response.status_code == 200

    response_2 = await client.post(
        "/coins/",
        json={"name": "Bitcoin", "symbol": "BTC", "price_per_unit": 123},
        headers={"access_token": access_token},
    )

    assert "Duplicate" in response_2.json()["detail"]
    assert response_2.status_code == 400


#  Test Deposit!
@pytest.mark.anyio
async def test_deposit_to_wallet(client, access_token, user, coin):
    response = await client.post(
        f"/deposit/?user_id={user.get('id')}&coin_id={coin.get('id')}&amount=120",
        headers={"access_token": access_token},
    )
    assert response.json()["amount"] == 120
    assert response.json()["user_id"] == user.get("id")
    assert response.json()["type"] == "Deposit"
    assert response.json()["coin_id"] == coin.get("id")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_deposit_to_wallet_without_token(client, user, coin):
    response = await client.post(
        f"/deposit/?user_id={user.get('id')}&coin_id={coin.get('id')}&amount=120",
    )

    assert (
        response.json()["message"] == "You are not authenticated to use this route..."
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_deposit_to_wallet_without_data(client, access_token, user, coin):
    response = await client.post("/deposit/", headers={"access_token": access_token})
    assert response.json()["detail"][0]["loc"][1] == "user_id"
    assert response.json()["detail"][1]["loc"][1] == "coin_id"
    assert response.json()["detail"][2]["loc"][1] == "amount"
    assert response.status_code == 422


@pytest.mark.anyio
async def test_deposit_to_wallet_with_wrong_data(client, access_token, user, coin):
    response = await client.post(
        f"/deposit/?user_id={user.get('id')}&coin_id=5&amount=120",
        headers={"access_token": access_token},
    )

    assert response.json()["detail"] == "Coin not found."
    assert response.status_code == 404

    response = await client.post(
        f"/deposit/?user_id=4&coin_id={coin.get('id')}&amount=120",
        headers={"access_token": access_token},
    )

    assert response.json()["detail"] == "Wallet not found for user."
    assert response.status_code == 404

    response = await client.post(
        f"/deposit/?user_id={user.get('id')}&coin_id={coin.get('id')}&amount=-120",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Price Should be greate than 0."
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_coin_empty_list(client):
    response = await client.get("/coins/")
    assert response.json() == []
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_coin(client, coin):
    response = await client.get(
        f"/get_coin?coin_id={coin.get('id')}",
    )
    assert response.json()["name"] == coin.get("name")
    assert response.json()["symbol"] == coin.get("symbol")
    assert response.json()["price_per_unit"] == coin.get("price_per_unit")
    assert response.json()["id"] == coin.get("id")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_coin_without_passing_id(client):
    response = await client.get(
        "/get_coin",
    )
    assert response.json()["detail"][0]["loc"][1] == "coin_id"
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_coin_without_wrong_id(client):
    response = await client.get(
        "/get_coin?coin_id=9",
    )
    assert response.json()["detail"] == "Coin Was Not Found!"
    assert response.status_code == 404


# test withdarw
@pytest.mark.anyio
async def test_withdraw_from_wallet(deposit, client, access_token):
    response = await client.post(
        f"/withdraw/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}",
        headers={"access_token": access_token},
    )
    assert response.json()["type"] == "Withdraw"
    assert response.json()["amount"] == deposit.get("amount") - 10
    assert response.json()["user_id"] == deposit.get("user_id")
    assert response.json()["coin_id"] == deposit.get("coin_id")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_withdraw_from_wallet_more_than_availible_amount(
    deposit, client, access_token
):
    response = await client.post(
        f"/withdraw/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') + 10}",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Un-Sufficient Balance!"
    assert response.status_code == 404


@pytest.mark.anyio
async def test_withdraw_from_wallet_without_token(deposit, client):
    response = await client.post(
        f"/withdraw/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}"
    )
    assert (
        response.json()["message"] == "You are not authenticated to use this route..."
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_withdraw_from_wallet_without_data(client, access_token):
    response = await client.post("/withdraw/", headers={"access_token": access_token})
    assert response.json()["detail"][0]["loc"][1] == "user_id"
    assert response.json()["detail"][1]["loc"][1] == "coin_id"
    assert response.json()["detail"][2]["loc"][1] == "amount"
    assert response.status_code == 422


@pytest.mark.anyio
async def test_withdraw_from_wallet_with_wrong_data(client, access_token, deposit):
    response = await client.post(
        f"/withdraw/?user_id={deposit.get('user_id')}&coin_id=5&amount=120",
        headers={"access_token": access_token},
    )

    assert response.json()["detail"] == "Coin not found."
    assert response.status_code == 404

    response = await client.post(
        f"/withdraw/?user_id=4&coin_id={deposit.get('coin_id')}&amount=120",
        headers={"access_token": access_token},
    )

    assert response.json()["detail"] == "Wallet not found for user."
    assert response.status_code == 404

    response = await client.post(
        f"/withdraw/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount=-120",
        headers={"access_token": access_token},
    )

    assert response.json()["detail"] == "Price Should be greate than 0."
    assert response.status_code == 404

    response = await client.post(
        f"/withdraw/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') + 10}",
        headers={"access_token": access_token},
    )

    assert response.json()["detail"] == "Un-Sufficient Balance!"
    assert response.status_code == 404
