from fastapi import APIRouter
from app.database import get_db
from fastapi import Depends
from typing import List
from sqlmodel.ext.asyncio.session import AsyncSession
from app.services import UserServices, CoinServices, WalletServices

from app.models import *

router = APIRouter()

@router.get("/users", response_model=List[UserOut])
async def get_users(db: AsyncSession = Depends(get_db)):
    return await UserServices.get_users(db)

@router.get("/user-details", response_model=UserDetailedOut)
async def get_user_details(user_id: int, db: AsyncSession = Depends(get_db)):
    return await UserServices.get_user_details(user_id=user_id, db=db)

@router.post("/users/")
async def create_user(user: User, db: AsyncSession = Depends(get_db)):
    return await UserServices.create_user(user=user, db=db)

@router.get("/wallet/", response_model=Wallet)
async def get_wallet(user_id: int, db: AsyncSession = Depends(get_db)):
    return await WalletServices.get_wallet(user_id=user_id, db=db)

@router.post("/deposit/", response_model=Transaction)
async def deposit(user_id: int, coin_id: int, amount: float, db: AsyncSession = Depends(get_db)):
    return await WalletServices.deposit(user_id=user_id, coin_id=coin_id, amount=amount, db=db)

@router.get("/coins/", response_model=List[CoinOut])
async def list_coins(db: AsyncSession = Depends(get_db)):
    return await CoinServices.get_coins(db=db)

@router.post("/coins/", response_model=Coin)
async def add_coin(coin: Coin, db: AsyncSession = Depends(get_db)):
    return await CoinServices.add_coin(coin=coin, db=db)
