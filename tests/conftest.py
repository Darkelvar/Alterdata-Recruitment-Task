import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Base
from app.db.session import get_db
from app.db.session_sync import get_sync_db
from app.main import app

engine_test = create_async_engine(settings.DATABASE_URL_TEST)
AsyncSessionLocal = sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session


engine_test_sync = create_engine(settings.DATABASE_URL_TEST_SYNC)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test_sync)


def override_get_db_sync():
    with SessionLocal() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_sync_db] = override_get_db_sync


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post(
            "/api/v1/auth/token", data={"username": "admin", "password": "secret"}
        )
        response.raise_for_status()
        token = response.json()["access_token"]

        # Attach Authorization header
        ac.headers.update({"Authorization": f"Bearer {token}"})
        yield ac


@pytest.fixture
def sync_db():
    gen = override_get_db_sync()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


@pytest.fixture
async def async_db():
    agen = override_get_db()
    db = await agen.__anext__()
    try:
        yield db
    finally:
        try:
            await agen.__anext__()
        except StopAsyncIteration:
            pass


@pytest.fixture(autouse=True)
def clean_database(sync_db):
    sync_db.execute(text("SET session_replication_role = replica;"))
    sync_db.execute(text("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE;"))
    sync_db.execute(text("SET session_replication_role = origin;"))
    sync_db.commit()
