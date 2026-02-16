"""
PostgreSQL connection via SQLAlchemy async engine.
"""
import os
<<<<<<< HEAD
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
=======
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
>>>>>>> feature/threads

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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseEntity(Base):
    """
    Base for entities with common fields: id, created_at, updated_at, deleted_at.
    deleted_at is for soft delete: set to timestamp when "deleted", filter by IS NULL for active.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        """True if soft-deleted."""
        return self.deleted_at is not None


def active_only(entity_class: type[BaseEntity]):
    """Filter for non-deleted records. Usage: select(X).where(active_only(X))"""
    return entity_class.deleted_at.is_(None)


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

<<<<<<< HEAD
=======

>>>>>>> feature/threads
async def init_db() -> None:
    """Create all tables. Call on app startup if you use Base.metadata.create_all."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db() -> None:
    """Dispose engine. Call on app shutdown."""
    await engine.dispose()
