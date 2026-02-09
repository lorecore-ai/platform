"""Tenants module dependency providers. Wiring only."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.modules.agents.deps import get_agent_service
from app.modules.agents.service import AgentService
from app.modules.tenants.service import TenantService


def get_tenant_service(
    db: AsyncSession = Depends(get_db),
    agent_service: AgentService = Depends(get_agent_service),
) -> TenantService:
    """Request-scoped tenant service."""
    return TenantService(db, agent_service)
