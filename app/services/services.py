from app.models import *

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from sqlmodel import select
from sqlalchemy.orm import selectinload

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

import redis
import json

import jwt
from datetime import timedelta, timezone, datetime
from functools import wraps

jwt_config = {}
jwt_config['secret_key'] = "11223344"

class JWT_Services():
    
    @staticmethod  # Added missing @staticmethod decorator
    def create_token(user_id):
        payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }

        token = jwt.encode(payload, jwt_config['secret_key'], algorithm="HS256")
        return token

    @staticmethod
    def decode_token(token):
        try:
            decoded_token = jwt.decode(token, jwt_config['secret_key'], algorithms=["HS256"])
            return decoded_token.get("user_id")
        except jwt.ExpiredSignatureError:
            print("Token expired!")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token!")
            return None
    
    @staticmethod
    def jwt_required(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):  # Added async
            access_token = request.headers.get("access_token", "")
            if access_token:
                user_id = JWT_Services.decode_token(access_token)
                if user_id:
                    request.user_id = user_id
                    return await func(request, *args, **kwargs)  # Added await
                else:
                    raise HTTPException(status_code=403, detail="Token Is Not Valid! Please Login Again")
            else:
                raise HTTPException(status_code=403, detail="Token Not Found Please Login!")
        return wrapper
    
    @staticmethod
    async def login_user(email, password, request: Request, db: AsyncSession):
        # Fixed the query execution
        result = await db.exec(select(User).where(User.email == email, User.password == password))
        user: User = result.first()
        
        if user:
            token = JWT_Services.create_token(user.id)
            return JSONResponse(
                status_code=200, 
                content={
                    "message": "User Logged In Successfully!", 
                    "access_token": token
                }
            )
        else:
            raise HTTPException(status_code=404, detail="User Not Found!")
        
class UserServices:

    @staticmethod
    async def get_users(db: AsyncSession):
        users = await db.exec(select(User))
        return users


    @staticmethod
    async def get_user_details(user_id: int, db: AsyncSession):
        stmt = (
            select(User)
            .options(
                selectinload(User.wallet)
                .selectinload(Wallet.coins_wallet)
                .selectinload(CoinsWallet.coin_type),
                selectinload(User.transactions),
                selectinload(User.trades)
            )
            .where(User.id == user_id)
        )
        result = await db.exec(stmt)
        user = result.first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Build Wallet DTO
        wallet_out = None
        if user.wallet:
            coins_wallet_out = [
                CoinsWalletOut(
                    id=cw.id,
                    amount=cw.amount,
                    coin_type=CoinOut(
                        id=cw.coin_type.id,
                        name=cw.coin_type.name,
                        symbol=cw.coin_type.symbol,
                        price_per_unit=cw.coin_type.price_per_unit
                    )
                )
                for cw in user.wallet.coins_wallet
            ]
            wallet_out = WalletOut(
                id=user.wallet.id,
                name=user.wallet.name,
                coins_wallet=coins_wallet_out
            )

        # Transactions
        transactions_out = [
            TransactionOut(
                id=tx.id,
                type=tx.type,
                amount=tx.amount,
                timestamp=tx.timestamp,
                coin_id=tx.coin_id
            )
            for tx in sorted(user.transactions, key=lambda t: t.timestamp, reverse=True)[:10]
        ]

        # Trades
        trades_out = [
            TradeOut(
                id=tr.id,
                trade_type=tr.trade_type,
                price=tr.price,
                quantity=tr.quantity,
                timestamp=tr.timestamp,
                coin_id=tr.coin_id
            )
            for tr in sorted(user.trades, key=lambda t: t.timestamp, reverse=True)[:10]
        ]

        return UserDetailedOut(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            wallet=wallet_out,
            transactions=transactions_out,
            trades=trades_out
        )


    @staticmethod
    async def create_user(user: User, db: AsyncSession):
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            wallet = Wallet(user_id=user.id, name=user.first_name+" "+user.last_name)
            db.add(wallet)
            await db.commit()
            await db.refresh(wallet)
            return JSONResponse(status_code=201, content={"user": user.model_dump(), "wallet": wallet.model_dump()})
        except IntegrityError as e:
            db.rollback()
            s = str(e.orig).split("DETAIL:")[1].strip()
            raise HTTPException(status_code=404, detail=f"{s}")


class WalletServices:

    @staticmethod
    async def get_wallet(user_id, db: AsyncSession):
        result =  await db.exec(select(Wallet).options(selectinload(Wallet.coins_wallet).selectinload(CoinsWallet.coin_type)).where(Wallet.user_id == user_id))
        wallet = result.first()
        if wallet:
            coins_wallet_out = [
                CoinsWalletOut(
                    id=cw.id,
                    amount=cw.amount,
                    coin_type=CoinOut(
                        id=cw.coin_type.id,
                        name=cw.coin_type.name,
                        symbol=cw.coin_type.symbol,
                        price_per_unit=cw.coin_type.price_per_unit
                    )
                )
                for cw in wallet.coins_wallet
            ]
            return WalletOut(id=wallet.id, name= wallet.name, coins_wallet=coins_wallet_out)
        raise HTTPException(status_code=400, detail="User Does Not Exist!")
    
    @staticmethod
    async def deposit(coin_id: int, user_id: int, amount: float, db: AsyncSession):
        coin_result = await db.exec(select(Coin).where(Coin.id == coin_id))
        coin: Coin = coin_result.first()
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found.")
        
        wallet_result = await db.exec(select(Wallet).where(Wallet.user_id == user_id))
        wallet: Wallet = wallet_result.first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found for user.")
        
        coins_in_wallet = await db.exec(select(CoinsWallet).where(CoinsWallet.wallet_id==wallet.id))
        coins_in_wallet: List[CoinsWallet] = coins_in_wallet.all()
        coin_in_wallet = None
        coin_exist_in_wallet = False

        for coin_in_wallet_ in coins_in_wallet:
            if coin_in_wallet_.coin_type_id == coin_id:
                coin_in_wallet = coin_in_wallet_
                coin_exist_in_wallet = True
                break

        if not coin_exist_in_wallet:
            coin_wallet = CoinsWallet(coin_type_id=coin.id, wallet_id=wallet.id, amount=amount)
            db.add(coin_wallet)
            await db.commit()
            await db.refresh(coin_wallet)
        else:
            coin_in_wallet.amount += amount
            db.add(coin_in_wallet)
            await db.commit()
            await db.refresh(coin_in_wallet)

        # add transaction
        transacrion = Transaction(user_id=user_id, type="Deposit", amount=amount, coin_id=coin.id)
        db.add(transacrion)
        await db.commit()
        await db.refresh(transacrion)

        return transacrion

    @staticmethod
    async def withdraw(coin_id: int, user_id: int, amount: float, db: AsyncSession):
        coin_result = await db.exec(select(Coin).where(Coin.id == coin_id))
        coin: Coin = coin_result.first()
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found.")
        
        wallet_result = await db.exec(select(Wallet).where(Wallet.user_id == user_id))
        wallet: Wallet = wallet_result.first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found for user.")
        
        coins_in_wallet = await db.exec(select(CoinsWallet).where(CoinsWallet.wallet_id==wallet.id))
        coins_in_wallet: List[CoinsWallet] = coins_in_wallet.all()
        coin_in_wallet: CoinsWallet = None
        coin_exist_in_wallet = False

        for coin_in_wallet_ in coins_in_wallet:
            if coin_in_wallet_.coin_type_id == coin_id:
                coin_in_wallet = coin_in_wallet_
                coin_exist_in_wallet = True
                break

        if not coin_exist_in_wallet:
            raise HTTPException(status_code=404, detail="Un-Sufficient Balance!")
        else:
            if coin_in_wallet.amount > 0:
                if coin_in_wallet.amount >= amount:
                    coin_in_wallet.amount -= amount
                    db.add(coin_in_wallet)
                    await db.commit()
                    await db.refresh(coin_in_wallet)
                else:
                    raise HTTPException(status_code=404, detail="Un-Sufficient Balance!")
            else:
                raise HTTPException(status_code=404, detail="Un-Sufficient Balance!")

        # add transaction
        transacrion = Transaction(user_id=user_id, type="Withdraw", amount=amount, coin_id=coin.id)
        db.add(transacrion)
        await db.commit()
        await db.refresh(transacrion)

        return transacrion
        
class CoinServices:

    @staticmethod
    async def get_coins(db: AsyncSession):
        coins = await db.exec(select(Coin))
        return coins
    
    @staticmethod
    async def get_coin(coin_id: int, db: AsyncSession):
        coin = await db.exec(select(Coin).where(Coin.id==coin_id))
        coin = coin.first()
        if coin:
            return coin
        raise HTTPException(status_code=404, detail="Coin Was Not Found!")

    @staticmethod
    async def add_coin(coin: Coin, db: AsyncSession):
        try:
            db.add(coin)
            await db.commit()
            await db.refresh(coin)
            return coin
        except IntegrityError as e:
            db.rollback()
            s = str(e.orig).split("DETAIL:")[1].strip()
            raise HTTPException(status_code=400, detail=f"{s}")


class TradeServices:

    @staticmethod
    async def sell(coin_id: int, user_id: int, amount: float, price_per_unit: float, db: AsyncSession):
        """
        Creates a sell order for a specific coin
        """
        # Validate coin exists
        coin_result = await db.exec(select(Coin).where(Coin.id == coin_id))
        coin: Coin = coin_result.first()
        if not coin:
            raise HTTPException(status_code=404, detail="Coin not found.")
        
        # Get user's wallet
        wallet_result = await db.exec(select(Wallet).where(Wallet.user_id == user_id))
        wallet: Wallet = wallet_result.first()
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found for user.")
        
        # Check if user has the coin in their wallet
        coin_in_wallet_result = await db.exec(
            select(CoinsWallet).where(
                CoinsWallet.wallet_id == wallet.id,
                CoinsWallet.coin_type_id == coin_id
            )
        )
        coin_in_wallet: CoinsWallet = coin_in_wallet_result.first()

        if not coin_in_wallet or coin_in_wallet.amount < amount:
            raise HTTPException(status_code=400, detail="Insufficient balance!")

        # Validate price is within acceptable range (±10 from current price)
        if not (coin.price_per_unit - 10 <= price_per_unit <= coin.price_per_unit + 10):
            raise HTTPException(status_code=400, detail="Price must be within ±10 of current market price")

        # Deduct coins from wallet
        coin_in_wallet.amount -= amount
        db.add(coin_in_wallet)
        await db.commit()
        await db.refresh(coin_in_wallet)

        # Create sell trade record
        trade = Trade(
            user_id=user_id, 
            coin_id=coin_id, 
            trade_type="Sell", 
            price=price_per_unit,  # Use the price_per_unit parameter, not coin.price_per_unit
            quantity=amount
        )
        db.add(trade)
        await db.commit()
        await db.refresh(trade)

        # Create transaction record
        transaction = Transaction(
            user_id=user_id, 
            type="Withdraw-Trade", 
            amount=amount, 
            coin_id=coin_id
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return trade
    
    @staticmethod
    async def get_options(coin_id: int, db: AsyncSession):
        """
        Get all available sell orders for a specific coin
        """
        trades_result = await db.exec(
            select(Trade).where(
                Trade.coin_id == coin_id, 
                Trade.trade_type == "Sell"
            )
        )
        trades = trades_result.all()
        
        if not trades:
            raise HTTPException(status_code=404, detail="No sell orders available for this coin!")
        
        return trades
        
    @staticmethod
    async def buy(trade_id: int, your_wallet_id: int, coin_id: int, db: AsyncSession):
        """
        Buy coins from an existing sell order
        """
        # Get the sell trade
        trade_result = await db.exec(
            select(Trade).where(
                Trade.id == trade_id,
                Trade.trade_type == "Sell"
            )
        )
        trade: Trade = trade_result.first()

        if not trade:
            raise HTTPException(status_code=404, detail="Sell order not found or already completed.")
        
        # Get buyer's wallet with coin information
        wallet_result = await db.exec(
            select(Wallet)
            .options(selectinload(Wallet.coins_wallet).selectinload(CoinsWallet.coin_type))
            .where(Wallet.id == your_wallet_id)
        )
        wallet: Wallet = wallet_result.first()

        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found.")

        # Find the payment coin in buyer's wallet (assuming coin_id is the payment currency)
        payment_coin_wallet = next(
            (cw for cw in wallet.coins_wallet if cw.coin_type_id == coin_id), 
            None
        )

        if not payment_coin_wallet:
            raise HTTPException(status_code=404, detail="Payment currency not found in your wallet.")

        # Calculate total cost
        total_cost = trade.price * trade.quantity
        
        # Check if buyer has enough balance (in terms of value)
        buyer_balance_value = payment_coin_wallet.amount * payment_coin_wallet.coin_type.price_per_unit
        
        if total_cost > buyer_balance_value:
            raise HTTPException(status_code=400, detail="Insufficient balance to complete this purchase.")

        # Deduct payment from buyer's wallet
        payment_amount_in_coins = total_cost / payment_coin_wallet.coin_type.price_per_unit
        payment_coin_wallet.amount -= payment_amount_in_coins
        db.add(payment_coin_wallet)

        # Add purchased coins to buyer's wallet
        purchased_coin_wallet = next(
            (cw for cw in wallet.coins_wallet if cw.coin_type_id == trade.coin_id), 
            None
        )
        
        if purchased_coin_wallet:
            # Buyer already has this coin type
            purchased_coin_wallet.amount += trade.quantity
            db.add(purchased_coin_wallet)
        else:
            # Create new coin wallet entry for buyer
            new_coin_wallet = CoinsWallet(
                wallet_id=wallet.id,
                coin_type_id=trade.coin_id,
                amount=trade.quantity
            )
            db.add(new_coin_wallet)

        # Mark the sell trade as completed
        trade.trade_type = "Sell-Done"
        db.add(trade)

        # Create buy trade record
        buy_trade = Trade(
            user_id=wallet.user_id,
            coin_id=trade.coin_id,
            quantity=trade.quantity,
            price=trade.price,
            trade_type="Buy"
        )
        db.add(buy_trade)

        # Create transaction records
        # Buyer's payment transaction
        payment_transaction = Transaction(
            user_id=wallet.user_id,
            coin_id=coin_id,
            amount=payment_amount_in_coins,
            type="Withdraw-Trade"
        )
        db.add(payment_transaction)

        # Buyer's received coins transaction
        received_transaction = Transaction(
            user_id=wallet.user_id,
            coin_id=trade.coin_id,
            amount=trade.quantity,
            type="Deposit-Trade"
        )
        db.add(received_transaction)

        # Seller's payment received transaction
        seller_payment_transaction = Transaction(
            user_id=trade.user_id,
            coin_id=coin_id,
            amount=payment_amount_in_coins,
            type="Deposit-Trade"
        )
        db.add(seller_payment_transaction)

        # Commit all changes
        await db.commit()

        # Setting New Price For Coin
        coin = await db.exec(select(Coin).where(Coin.id==trade.coin_id))
        coin: Coin = coin.first()
        coin.price_per_unit = trade.price
        db.add(coin)

        await db.commit()
        
        # Refresh objects
        await db.refresh(buy_trade)
        await db.refresh(payment_transaction)
        await db.refresh(received_transaction)
        await db.refresh(seller_payment_transaction)
        await db.refresh(coin)

        return buy_trade
    

class WebsocketServices:

    @staticmethod
    async def get_price(coin_id: int, db: AsyncSession) -> Optional[float]:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        cached = r.get('coins')
        if not cached:
            result = await db.exec(select(Coin))
            coins: List[Coin] = result.all()
            coins_json = [coin.model_dump() for coin in coins]
            r.set('coins', json.dumps(coins_json))
            r.expire('coins', 1)
            for coin in coins:
                if coin.id == coin_id:
                    return coin.model_dump()
        else:
            coins = json.loads(cached)
            for coin in coins:
                if coin["id"] == coin_id:
                    return coin
        return None 