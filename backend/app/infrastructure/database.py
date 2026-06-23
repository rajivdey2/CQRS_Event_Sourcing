from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.async_database_url,   # handles postgres:// → postgresql+asyncpg://
    echo=settings.sql_echo,
    pool_size=5,                   # Render free tier: max 10 connections
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,              # recycle connections every 5 min
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session