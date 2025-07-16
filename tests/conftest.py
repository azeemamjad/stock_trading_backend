import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.sql import text
from sqlmodel.ext.asyncio.session import AsyncSession
from app.main import app
from app.routes import get_db

pytest_plugins = ["tests.fixtures.global_fixtures"]

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with AsyncSessionLocal() as session:
        try:
            # Start a nested transaction (rolls back everything after test)
            await session.begin_nested()
            yield session
        finally:
            # Rollback all changes to ensure clean state
            await session.rollback()

            # Optional: Reset auto-increment counters (SQLite-specific)
            for table in reversed(SQLModel.metadata.sorted_tables):
                await session.exec(text(f"DELETE FROM {table.name}"))
            await session.commit()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.rollback()  # Ensure no lingering transactions

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
