"""Agent runtime dependency providers."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.modules.secrets.base import SecretsManager
from app.modules.secrets.deps import get_secrets
from app.modules.agent_runtime.service import AgentRuntimeService
from app.modules.threads.service import MessageService


def get_agent_runtime_service(
    db: AsyncSession = Depends(get_db),
    secrets: SecretsManager = Depends(get_secrets),
) -> AgentRuntimeService:
    """Request-scoped agent runtime service."""
    return AgentRuntimeService(
        session=db,
        secrets=secrets,
        message_service=MessageService(db),
    )
