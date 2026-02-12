"""Agent service: DB operations for agents."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.models import Agent, AgentType
from app.modules.agents.schemas import AgentCreate, AgentUpdate

PLATFORM_SYSTEM_AGENT_NAME = "Assistant"


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

    async def get_platform_llm_agents(self) -> list[Agent]:
        """Platform LLM agents (tenant_id is None): system and worker."""
        result = await self._session.execute(
            select(Agent)
            .where(
                Agent.tenant_id.is_(None),
                Agent.type.in_((AgentType.System, AgentType.Worker)),
            )
            .order_by(Agent.id)
        )
        return list(result.scalars().all())

    async def get_available_for_tenant(self, tenant_id: uuid.UUID) -> list[Agent]:
        """Tenant agents + platform LLM agents for thread creation."""
        tenant_agents = await self.get_by_tenant(tenant_id)
        platform_agents = await self.get_platform_llm_agents()
        return tenant_agents + platform_agents

    async def update(self, agent: Agent, data: AgentUpdate) -> Agent:
        if data.name is not None:
            agent.name = data.name
        if data.type is not None:
            agent.type = data.type
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def create(self, tenant_id: uuid.UUID, data: AgentCreate) -> Agent:
        agent = Agent(
            tenant_id=tenant_id,
            name=data.name,
            type=data.type,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def create_human_for_tenant(self, tenant_id: uuid.UUID) -> Agent:
        """Create user (human) agent for a new tenant. Used when tenant is created."""
        agent = Agent(
            tenant_id=tenant_id,
            name="User",
            type=AgentType.Human,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def ensure_platform_llm_agent(self) -> Agent:
        """Create platform LLM agent if not exists. Used at startup."""
        existing = await self.get_platform_llm_agents()
        if existing:
            return existing[0]
        agent = Agent(
            tenant_id=None,
            name=PLATFORM_SYSTEM_AGENT_NAME,
            type=AgentType.System,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent
