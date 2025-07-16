from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, HTTPException
from app.database import get_db
from fastapi import Depends
from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services import (
    UserServices,
    CoinServices,
    WalletServices,
    TradeServices,
    WebsocketServices,
)

import asyncio
from sqlmodel import select

import jwt
from datetime import datetime, timezone, timedelta

from app.models import (
    TradeOut,
    User,
    UserDetailedOut,
    UserOut,
    Transaction,
    Coin,
    CoinOut,
)
from fastapi.responses import JSONResponse
from functools import wraps

router = APIRouter()


class JWT_Management:
    @staticmethod
    async def login(email, password, db: AsyncSession):
        user = await db.exec(
            select(User).where(User.email == email, User.password == password)
        )
        user = user.first()
        if user:
            token = JWT_Management.create_token(user.id)
            id = JWT_Management.decode_token(token)
            return JSONResponse(status_code=200, content={"token": token, "id": id})
        else:
            raise HTTPException(status_code=404, detail="User Not Found!")

    @staticmethod
    def create_token(id):
        payload = {
            "id": id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }

        encoded = jwt.encode(payload=payload, key="1122", algorithm="HS256")

        return encoded

    @staticmethod
    def decode_token(token):
        try:
            decoded_token = jwt.decode(token, "1122", algorithms=["HS256"])
            return decoded_token.get("id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def require_jwt(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or next(
                (arg for arg in args if isinstance(arg, Request)), None
            )
            db: AsyncSession = kwargs.get("db") or next(
                (arg for arg in args if isinstance(arg, AsyncSession)), None
            )
            token = request.headers.get("access_token", "")
            user_id = JWT_Management.decode_token(token)
            user = await db.exec(select(User).where(User.id == user_id))
            user = user.first()
            if user:
                return await func(*args, **kwargs)
            else:
                return JSONResponse(
                    status_code=403,
                    content={
                        "message": "You are not authenticated to use this route..."
                    },
                )

        return wrapper


@router.post("/login")
async def login_user(
    email: str, password: str, request: Request, db: AsyncSession = Depends(get_db)
):
    return await JWT_Management.login(email=email, password=password, db=db)


@router.get("/users", response_model=List[UserOut])
@JWT_Management.require_jwt
async def get_users(request: Request, db: AsyncSession = Depends(get_db)):
    return await UserServices.get_users(db)


@router.get("/user-details", response_model=UserDetailedOut)
@JWT_Management.require_jwt
async def get_user_details(
    user_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    return await UserServices.get_user_details(user_id=user_id, db=db)


@router.post("/users/")
async def create_user(user: User, db: AsyncSession = Depends(get_db)):
    return await UserServices.create_user(user=user, db=db)


@router.get("/wallet/")
@JWT_Management.require_jwt
async def get_wallet(
    user_id: int, request: Request, db: AsyncSession = Depends(get_db)
):
    return await WalletServices.get_wallet(user_id=user_id, db=db)


@router.post("/deposit/", response_model=Transaction)
@JWT_Management.require_jwt
async def deposit(
    user_id: int,
    coin_id: int,
    amount: float,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await WalletServices.deposit(
        user_id=user_id, coin_id=coin_id, amount=amount, db=db
    )


@router.post("/withdraw/", response_model=Transaction)
@JWT_Management.require_jwt
async def withdraw(
    user_id: int,
    coin_id: int,
    amount: float,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await WalletServices.withdraw(
        user_id=user_id, coin_id=coin_id, amount=amount, db=db
    )


@router.get("/coins/", response_model=List[CoinOut])
async def list_coins(db: AsyncSession = Depends(get_db)):
    return await CoinServices.get_coins(db=db)


@router.post("/coins/")
@JWT_Management.require_jwt
async def add_coin(coin: Coin, request: Request, db: AsyncSession = Depends(get_db)):
    return await CoinServices.add_coin(coin=coin, db=db)


@router.get("/get_coin")
async def get_coin(coin_id: int, db: AsyncSession = Depends(get_db)):
    return await CoinServices.get_coin(coin_id, db)


@router.post("/sell/", response_model=TradeOut)
@JWT_Management.require_jwt
async def sell(
    user_id: int,
    coin_id: int,
    amount: float,
    price_per_unit: float,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await TradeServices.sell(
        user_id=user_id,
        coin_id=coin_id,
        amount=amount,
        price_per_unit=price_per_unit,
        db=db,
    )


@router.get("/purchase-options", response_model=List[TradeOut])
async def purchase_options(coin_id: int, db: AsyncSession = Depends(get_db)):
    return await TradeServices.get_options(coin_id, db=db)


@router.post("/buy/")
@JWT_Management.require_jwt
async def buy(
    trade_id: int,
    your_wallet_id: int,
    coin_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await TradeServices.buy(
        trade_id=trade_id, your_wallet_id=your_wallet_id, coin_id=coin_id, db=db
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        try:
            coin_id = int(data)
        except ValueError:
            await websocket.send_text("Invalid coin ID")
            return
        while True:
            price = await WebsocketServices.get_price(coin_id=coin_id, db=db)
            await websocket.send_text(f"{price}")
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
