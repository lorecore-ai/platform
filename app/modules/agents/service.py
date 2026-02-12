"""Agent service: DB operations for agents."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.models import Agent, AgentType
from app.modules.agents.schemas import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        result = await self._session.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[Agent]:
        result = await self._session.execute(
            select(Agent).where(Agent.tenant_id == tenant_id).order_by(Agent.id)
        )
        return list(result.scalars().all())

    async def update(self, agent: Agent, data: AgentUpdate) -> Agent:
        if data.name is not None:
            agent.name = data.name
        if data.type is not None:
            agent.type = data.type
        if data.model is not None:
            agent.model = data.model
        if data.system_prompt is not None:
            agent.system_prompt = data.system_prompt
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

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
            model="gpt-4o-mini",
            system_prompt="",
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent
