from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship, Column, String, DateTime
from sqlalchemy import UniqueConstraint


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    first_name: str
    last_name: str
    email: str = Field(sa_column=Column(String(100), unique=True, index=True))
    password: str = Field(sa_column=Column(String(128)))

    wallet: "Wallet" = Relationship(back_populates="user")
    trades: List["Trade"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")

class Wallet(SQLModel, table=True):
    __tablename__ = "wallets"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True)
    name: str

    user: Optional[User] = Relationship(back_populates="wallet")
    coins_wallet: List["CoinsWallet"] = Relationship(back_populates="wallet", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Coin(SQLModel, table=True):
    __tablename__ = "coin_types"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(sa_column=Column(String(50), unique=True, nullable=False))
    symbol: str = Field(sa_column=Column(String(10), unique=True, nullable=False))
    price_per_unit: float = Field(default=0.0)

    wallets: List["CoinsWallet"] = Relationship(back_populates="coin_type")
    trades: List["Trade"] = Relationship(back_populates="cointype")


class CoinsWallet(SQLModel, table=True):
    __tablename__ = "coins_wallet"
    __table_args__ = (UniqueConstraint("wallet_id", "coin_type_id", name="uix_wallet_coin_type"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    wallet_id: int = Field(foreign_key="wallets.id")
    coin_type_id: int = Field(foreign_key="coin_types.id")
    amount: float = Field(default=0.0)

    wallet: Wallet = Relationship(back_populates="coins_wallet")
    coin_type: Coin = Relationship(back_populates="wallets")

class Trade(SQLModel, table=True):
    __tablename__ = "trades"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id")
    coin_id: int = Field(foreign_key="coin_types.id")
    trade_type: str = Field(sa_column=Column(String(20)))
    price: float
    quantity: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship(back_populates="trades")
    cointype: Coin = Relationship(back_populates="trades")

class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    type: str = Field(sa_column=Column(String(20)))
    amount: float
    coin_id: int = Field(foreign_key="coin_types.id")
    timestamp: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))

    user: User = Relationship(back_populates="transactions")


# output schemas

class CoinOut(SQLModel):
    id: int
    name: str
    symbol: str
    price_per_unit: float

    class Config:
        from_attributes = True

class CoinsWalletOut(SQLModel):
    id: int
    coin_type: CoinOut
    amount: float

    class Config:
        from_attributes = True

class WalletOut(SQLModel):
    id: int
    name: str
    coins_wallet: List[CoinsWalletOut] = []

    class Config:
        from_attributes = True

class TransactionOut(SQLModel):
    id: int
    type: str
    amount: float
    timestamp: datetime
    coin_id: int

    class Config:
        from_attributes = True

class TradeOut(SQLModel):
    id: int
    trade_type: str
    price: float
    quantity: float
    timestamp: datetime
    coin_id: int

    class Config:
        from_attributes = True

class UserDetailedOut(SQLModel):
    id: int
    first_name: str
    last_name: str
    email: str
    wallet: Optional[WalletOut]
    transactions: List[TransactionOut] = []
    trades: List[TradeOut] = []

    class Config:
        from_attributes = True

class UserOut(SQLModel):
    id: int
    first_name: str
    last_name: str
    email: str
