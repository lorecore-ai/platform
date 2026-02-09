"""Tenant service: DB operations for tenants."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.service import AgentService
from app.modules.tenants.models import Tenant
from app.modules.tenants.schemas import TenantCreate


class TenantService:
    def __init__(self, session: AsyncSession, agent_service: AgentService) -> None:
        self._session = session
        self._agent_service = agent_service

    async def get_tenants(self) -> list[Tenant]:
        result = await self._session.execute(select(Tenant).order_by(Tenant.id))
        return list(result.scalars().all())

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        tenant = Tenant(name=data.name)
        self._session.add(tenant)
        await self._session.flush()
        await self._session.refresh(tenant)

        await self._agent_service.create_default_for_tenant(tenant.id)

        return tenant
