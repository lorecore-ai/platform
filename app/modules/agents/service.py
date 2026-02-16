"""Agent service: DB operations for agents."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.models import Agent, AgentNature
from app.modules.agents.schemas import AgentCreate, AgentUpdate

PLATFORM_SYSTEM_AGENT_FIRST_NAME = "Assistant"
PLATFORM_SYSTEM_AGENT_SECOND_NAME = ""


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
                Agent.nature.in_((AgentNature.System, AgentNature.Worker)),
            )
            .order_by(Agent.id)
        )
        return list(result.scalars().all())

    async def get_available_for_tenant(self, tenant_id: uuid.UUID) -> list[Agent]:
        """Tenant agents + platform LLM agents for thread creation."""
        tenant_agents = await self.get_by_tenant(tenant_id)
        return tenant_agents

    async def update(self, agent: Agent, data: AgentUpdate) -> Agent:
        if data.first_name is not None:
            agent.first_name = data.first_name
        if data.second_name is not None:
            agent.second_name = data.second_name
        if data.email is not None:
            agent.email = data.email
        if data.nature is not None:
            agent.nature = data.nature
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def create(self, tenant_id: uuid.UUID, data: AgentCreate) -> Agent:
        agent = Agent(
            tenant_id=tenant_id,
            first_name=data.first_name,
            second_name=data.second_name,
            email=data.email,
            nature=data.nature,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def create_human_for_tenant(self, tenant_id: uuid.UUID) -> Agent:
        """Create user (human) agent for a new tenant. Used when tenant is created."""
        agent = Agent(
            tenant_id=tenant_id,
            first_name="User",
            second_name="",
            nature=AgentNature.Human,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def create_system_for_tenant(self, tenant_id: uuid.UUID) -> Agent:
        """Create system agent for tenant. Answers questions in threads."""
        agent = Agent(
            tenant_id=tenant_id,
            first_name=PLATFORM_SYSTEM_AGENT_FIRST_NAME,
            second_name=PLATFORM_SYSTEM_AGENT_SECOND_NAME,
            nature=AgentNature.System,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent

    async def get_system_agent_for_tenant(self, tenant_id: uuid.UUID) -> Agent | None:
        """Get tenant's system agent (for LLM responses). Fallback to platform agent."""
        result = await self._session.execute(
            select(Agent)
            .where(
                Agent.tenant_id == tenant_id,
                Agent.nature == AgentNature.System,
            )
            .limit(1)
        )
        agent = result.scalar_one_or_none()
        if agent:
            return agent
        # Fallback: platform system agent (for tenants created before per-tenant agents)
        platform = await self.get_platform_llm_agents()
        return platform[0] if platform else None

    async def get_by_origin(
        self, origin_type: str, origin_id: str, tenant_id: uuid.UUID | None = None
    ) -> Agent | None:
        """Find agent by integration origin. For use in connectors."""
        q = select(Agent).where(
            Agent.origin_type == origin_type,
            Agent.origin_id == origin_id,
        )
        if tenant_id is not None:
            q = q.where(Agent.tenant_id == tenant_id)
        result = await self._session.execute(q.limit(1))
        return result.scalar_one_or_none()

    async def get_human_agent_for_tenant(self, tenant_id: uuid.UUID) -> Agent | None:
        """Get tenant's human agent (for user messages)."""
        result = await self._session.execute(
            select(Agent)
            .where(
                Agent.tenant_id == tenant_id,
                Agent.nature == AgentNature.Human,
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def ensure_platform_llm_agent(self) -> Agent:
        """Create platform LLM agent if not exists. Used at startup."""
        existing = await self.get_platform_llm_agents()
        if existing:
            return existing[0]
        agent = Agent(
            tenant_id=None,
            first_name=PLATFORM_SYSTEM_AGENT_FIRST_NAME,
            second_name=PLATFORM_SYSTEM_AGENT_SECOND_NAME,
            nature=AgentNature.System,
        )
        self._session.add(agent)
        await self._session.flush()
        await self._session.refresh(agent)
        return agent
