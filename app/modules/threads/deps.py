"""Threads module dependency providers."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.modules.secrets.deps import get_secrets
from app.modules.secrets.base import SecretsManager
from app.modules.threads.langchain_service import LangChainService
from app.modules.threads.service import MessageService, ThreadService


def get_thread_service(db: AsyncSession = Depends(get_db)) -> ThreadService:
    """Request-scoped thread service."""
    return ThreadService(db)


def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    """Request-scoped message service."""
    return MessageService(db)


def get_langchain_service(
    db: AsyncSession = Depends(get_db),
    secrets: SecretsManager = Depends(get_secrets),
) -> LangChainService:
    """Request-scoped LangChain service."""
    return LangChainService(db, secrets)
