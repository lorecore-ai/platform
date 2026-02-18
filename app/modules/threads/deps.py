"""Threads module dependency providers."""
import warnings

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.modules.secrets.deps import get_secrets
from app.modules.secrets.base import SecretsManager
from app.modules.agent_runtime.deps import get_agent_runtime_service as _get_runtime
from app.modules.agent_runtime.service import AgentRuntimeService
from app.modules.threads.langchain_service import LangChainService
from app.modules.threads.service import MessageService, ThreadService


def get_thread_service(db: AsyncSession = Depends(get_db)) -> ThreadService:
    """Request-scoped thread service."""
    return ThreadService(db)


def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    """Request-scoped message service."""
    return MessageService(db)


def get_agent_runtime_service(
    db: AsyncSession = Depends(get_db),
    secrets: SecretsManager = Depends(get_secrets),
) -> AgentRuntimeService:
    """Request-scoped AgentRuntimeService (LangGraph-based)."""
    return _get_runtime(db=db, secrets=secrets)


def get_langchain_service(
    db: AsyncSession = Depends(get_db),
    secrets: SecretsManager = Depends(get_secrets),
) -> LangChainService:
    """Request-scoped LangChain service.

    .. deprecated::
        Use ``get_agent_runtime_service`` instead. This provider will be
        removed in a future release.
    """
    warnings.warn(
        "get_langchain_service is deprecated, use get_agent_runtime_service",
        DeprecationWarning,
        stacklevel=2,
    )
    return LangChainService(db, secrets)
