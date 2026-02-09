"""Agent service: DB operations for agents."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.models import Agent, AgentType
from app.modules.agents.schemas import AgentCreate


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[Agent]:
        result = await self._session.execute(
            select(Agent).where(Agent.tenant_id == tenant_id).order_by(Agent.id)
        )
        return list(result.scalars().all())

    async def create(self, tenant_id: uuid.UUID, data: AgentCreate) -> Agent:
        agent = Agent(
            tenant_id=tenant_id,
            name=data.name,
            type=data.type,
            model=data.model,
            system_prompt=data.system_prompt,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def create_default_for_tenant(self, tenant_id: uuid.UUID) -> Agent:
        """Create default (main) agent for a new tenant. Used when tenant is created."""
        agent = Agent(
            tenant_id=tenant_id,
            name="Main",
            type=AgentType.Main,
            model="gpt-5o-mini",
            system_prompt="",
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent
