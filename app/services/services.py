from app.models import *

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from sqlmodel import select
from sqlalchemy.orm import selectinload

from fastapi import HTTPException
from fastapi.responses import JSONResponse

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
            return JSONResponse(status_code=200, content={"user": user.model_dump(), "wallet": wallet.model_dump()})
        except IntegrityError as e:
            db.rollback()
            s = str(e.orig).split("DETAIL:")[1].strip()
            raise HTTPException(status_code=404, detail=f"{s}")


class WalletServices:

    @staticmethod
    async def get_wallet(user_id, db: AsyncSession):
        result =  await db.exec(select(Wallet).where(Wallet.user_id == user_id))
        wallet = result.first()
        if wallet:
            return wallet
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
        
        coins_in_wallet = await db.exec(select(CoinsWallet).where(Wallet.id==wallet.id))
        coins_in_wallet: CoinsWallet = coins_in_wallet.all()
        coin_in_wallet = None
        coin_exist_in_wallet = False

        for coin_in_wallet_ in coins_in_wallet:
            if coin_in_wallet_.coin_type_id == coin_id and coin_in_wallet_.wallet_id == wallet.id:
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
        
class CoinServices:

    @staticmethod
    async def get_coins(db: AsyncSession):
        coins = await db.exec(select(Coin))
        return coins

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
        