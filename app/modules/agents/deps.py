"""Agents module dependency providers. Wiring only."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.modules.agents.service import AgentService


def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    """Request-scoped agent service."""
    return AgentService(db)
