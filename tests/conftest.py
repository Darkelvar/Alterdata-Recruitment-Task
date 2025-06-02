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


@pytest.fixture(scope="session")
def session_async_engine():
    return create_async_engine(settings.DATABASE_URL_TEST)


@pytest.fixture
def async_engine():
    return create_async_engine(settings.DATABASE_URL_TEST)


@pytest.fixture
def sync_engine():
    return create_engine(settings.DATABASE_URL_TEST_SYNC)


@pytest.fixture
def sync_session_factory(sync_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


@pytest.fixture
async def async_db(async_engine):
    session_factory = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def sync_db(sync_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    with Session() as session:
        yield session


@pytest.fixture(autouse=True)
def override_dependencies(async_db, sync_engine):
    async def _override_get_db():
        yield async_db

    def _override_get_db_sync():
        Session = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
        with Session() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_sync_db] = _override_get_db_sync


@pytest.fixture(scope="session", autouse=True)
async def prepare_test_db(session_async_engine):
    async with session_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with session_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def clean_database(sync_db):
    yield
    sync_db.execute(text("SET session_replication_role = replica;"))
    sync_db.execute(text("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE;"))
    sync_db.execute(text("SET session_replication_role = origin;"))
    sync_db.commit()


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        response = await ac.post(
            "/api/v1/auth/token", data={"username": "admin", "password": "secret"}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        ac.headers.update({"Authorization": f"Bearer {token}"})
        yield ac


@pytest.fixture
def anyio_backend():
    return "asyncio"
