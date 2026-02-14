"""
PostgreSQL connection via SQLAlchemy async engine.
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres",
)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "0") == "1",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Base class for ORM models."""

    pass


@asynccontextmanager
async def session_context() -> AsyncGenerator[AsyncSession, None]:
    """Single place that uses async_session_factory. Use get_db() in request handlers."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI: yields an async session and closes it after use."""
    async with session_context() as session:
        yield session


async def init_db() -> None:
    """Create all tables. Call on app startup if you use Base.metadata.create_all."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db() -> None:
    """Dispose engine. Call on app shutdown."""
    await engine.dispose()
