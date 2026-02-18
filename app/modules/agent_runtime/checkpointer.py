"""PostgreSQL checkpointer for LangGraph state persistence."""
from __future__ import annotations

import logging
import os

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)

_saver: AsyncPostgresSaver | None = None


def _get_connection_string() -> str:
    """Derive a psycopg-compatible connection string from DATABASE_URL.

    DATABASE_URL uses asyncpg driver (postgresql+asyncpg://...) but
    the LangGraph postgres checkpointer uses psycopg, so we strip
    the driver suffix.
    """
    url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@postgres:5432/postgres",
    )
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def get_checkpointer() -> AsyncPostgresSaver:
    """Return a singleton AsyncPostgresSaver, creating tables on first call."""
    global _saver
    if _saver is not None:
        return _saver

    conn_str = _get_connection_string()
    _saver = AsyncPostgresSaver.from_conn_string(conn_str)
    await _saver.setup()
    logger.info("LangGraph PostgreSQL checkpointer initialized")
    return _saver


async def close_checkpointer() -> None:
    """Cleanup on shutdown."""
    global _saver
    if _saver is not None:
        _saver = None
        logger.info("LangGraph checkpointer closed")
