import pytest


# Sell Stock
@pytest.mark.anyio
async def test_sell_stock(client, access_token, deposit):
    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}&price_per_unit={deposit.get('price_per_unit')}",
        headers={"access_token": access_token},
    )
    assert response.json()["trade_type"] == "Sell"
    assert response.json()["coin_id"] == deposit.get("coin_id")
    assert response.json()["quantity"] == deposit.get("amount") - 10
    assert response.json()["price"] == deposit.get("price_per_unit")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_sell_stock_with_more_or_less_than_10_price_per_unit(
    client, access_token, deposit
):
    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}&price_per_unit={deposit.get('price_per_unit') + 11}",
        headers={"access_token": access_token},
    )
    assert (
        response.json()["detail"] == "Price must be within ±10 of current market price"
    )
    assert response.status_code == 400

    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}&price_per_unit={deposit.get('price_per_unit') - 11}",
        headers={"access_token": access_token},
    )
    assert (
        response.json()["detail"] == "Price must be within ±10 of current market price"
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_sell_stock_with_more_amount_then_availible(
    client, access_token, deposit
):
    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') + 40}&price_per_unit={deposit.get('price_per_unit')}",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Insufficient balance!"
    assert response.status_code == 400


@pytest.mark.anyio
async def test_sell_stock_without_data(client, access_token):
    response = await client.post("/sell/", headers={"access_token": access_token})
    assert response.json()["detail"][0]["loc"][1] == "user_id"
    assert response.json()["detail"][1]["loc"][1] == "coin_id"
    assert response.json()["detail"][2]["loc"][1] == "amount"
    assert response.json()["detail"][3]["loc"][1] == "price_per_unit"
    assert response.status_code == 422


@pytest.mark.anyio
async def test_sell_stock_with_wrong_data(client, access_token, deposit):
    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount=-7&price_per_unit={deposit.get('price_per_unit')}",
        headers={"access_token": access_token},
    )
    assert (
        response.json()["detail"]
        == "Amount and Price Per Unit Should be greater than 0."
    )
    assert response.status_code == 404

    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}&price_per_unit=-10",
        headers={"access_token": access_token},
    )
    assert (
        response.json()["detail"]
        == "Amount and Price Per Unit Should be greater than 0."
    )
    assert response.status_code == 404

    response = await client.post(
        f"/sell/?user_id=17&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}&price_per_unit={deposit.get('price_per_unit')}",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Wallet not found for user."
    assert response.status_code == 404

    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id=11&amount={deposit.get('amount') - 10}&price_per_unit=-10",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Coin not found."
    assert response.status_code == 404


@pytest.mark.anyio
async def test_sell_stock_without_token(client, deposit):
    response = await client.post(
        f"/sell/?user_id={deposit.get('user_id')}&coin_id={deposit.get('coin_id')}&amount={deposit.get('amount') - 10}&price_per_unit={deposit.get('price_per_unit')}",
    )
    assert (
        response.json()["message"] == "You are not authenticated to use this route..."
    )
    assert response.status_code == 403


# Get Buy Options
@pytest.mark.anyio
async def test_get_options(client, stock):
    response = await client.get(f"/purchase-options?coin_id={stock.get('coin_id')}")
    response.json()[0]["id"] == stock.get("id")
    response.json()[0]["coin_id"] == stock.get("coin_id")
    response.json()[0]["quantity"] == stock.get("quantity")
    response.json()[0]["price"] == stock.get("price")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_options_with_wrong_data(client, stock):
    response = await client.get("/purchase-options?coin_id=3")
    assert response.json()["detail"] == "No sell orders available for this coin!"
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_options_with_without_coin_id(client, stock):
    response = await client.get("/purchase-options")
    assert response.json()["detail"][0]["loc"][1] == "coin_id"
    assert response.status_code == 422


# Buy Stock


@pytest.mark.anyio
async def test_buy_stock(client, access_token, wallet_id, deposit_2, stock):
    response = await client.post(
        f"/buy/?trade_id={stock.get('id')}&your_wallet_id={wallet_id.get('wallet_id')}&coin_id={deposit_2.get('coin_id')}",
        headers={"access_token": access_token},
    )
    assert response.json()["quantity"] == stock.get("quantity")
    assert response.json()["price"] == stock.get("price")
    assert response.json()["trade_type"] == "Buy"
    assert response.json()["coin_id"] == stock.get("coin_id")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_buy_stock_with_wrong_ids(
    client, access_token, wallet_id, deposit_2, stock
):
    response = await client.post(
        f"/buy/?trade_id=7&your_wallet_id={wallet_id.get('wallet_id')}&coin_id={deposit_2.get('coin_id')}",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Sell order not found or already completed."
    assert response.status_code == 404

    response = await client.post(
        f"/buy/?trade_id={stock.get('id')}&your_wallet_id=5&coin_id={deposit_2.get('coin_id')}",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Wallet not found."
    assert response.status_code == 404

    response = await client.post(
        f"/buy/?trade_id={stock.get('id')}&your_wallet_id={wallet_id.get('wallet_id')}&coin_id=9",
        headers={"access_token": access_token},
    )
    assert response.json()["detail"] == "Payment currency not found in your wallet."
    assert response.status_code == 404


@pytest.mark.anyio
async def test_buy_stock_with_low_money(
    client, access_token, wallet_id, deposit_3, stock
):
    response = await client.post(
        f"/buy/?trade_id={stock.get('id')}&your_wallet_id={wallet_id.get('wallet_id')}&coin_id={deposit_3.get('coin_id')}",
        headers={"access_token": access_token},
    )
    assert (
        response.json()["detail"] == "Insufficient balance to complete this purchase."
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_buy_stock_and_test_the_coin_price(
    client, access_token, wallet_id, deposit_2, stock
):
    response = await client.get(f"/get_coin?coin_id={stock.get('coin_id')}")
    response_1 = await client.post(
        f"/buy/?trade_id={stock.get('id')}&your_wallet_id={wallet_id.get('wallet_id')}&coin_id={deposit_2.get('coin_id')}",
        headers={"access_token": access_token},
    )
    response_2 = await client.get(f"/get_coin?coin_id={stock.get('coin_id')}")
    assert response_2.json()["id"] == stock.get("coin_id")
    assert response_2.json()["price_per_unit"] == stock.get("price")
    assert response.json()["price_per_unit"] != response_2.json()["price_per_unit"]
    assert response_1.status_code == 200
