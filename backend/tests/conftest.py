import asyncio
import pytest
import pytest_asyncio
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

# ── Reuse the same event loop for the whole test session ──────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory-style test DB (real Postgres via env var, or SQLite stub) ───────
TEST_DB_URL = "postgresql+asyncpg://ledger:ledger@localhost:5432/ledger_test"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)

    # Bootstrap schema from init.sql
    import os
    sql_path = os.path.join(os.path.dirname(__file__), "../../infra/init.sql")
    with open(sql_path) as f:
        ddl = f.read()

    async with engine.begin() as conn:
        await conn.execute(text(ddl))

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine) -> AsyncSession:
    """Each test gets a session that is rolled back after the test."""
    async with test_engine.connect() as conn:
        await conn.begin()
        session_factory = async_sessionmaker(bind=conn, expire_on_commit=False)
        async with session_factory() as s:
            yield s
        await conn.rollback()


@pytest_asyncio.fixture
async def client(test_engine):
    """Full ASGI test client wired to the test DB."""
    # Override DB URL before importing app
    import os
    os.environ["DATABASE_URL"] = TEST_DB_URL

    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c