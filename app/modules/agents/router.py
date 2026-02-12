"""Agents API router."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.agents.deps import get_agent_service
from app.modules.agents.models import AgentType
from app.modules.agents.schemas import AgentCreate, AgentRead, AgentUpdate
from app.modules.agents.service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/tenant/{tenant_id}",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent(
    tenant_id: uuid.UUID,
    data: AgentCreate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    if data.type != AgentType.Human:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant can only create human agents; system/worker agents are platform-managed",
        )
    agent = await service.create(tenant_id, data)
    return AgentRead.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    agent = await service.get_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    if agent.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform agents cannot be updated",
        )
    if data.type is not None and data.type != AgentType.Human:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant agents must remain human type",
        )
    agent = await service.update(agent, data)
    return AgentRead.model_validate(agent)


@router.get("/tenant/{tenant_id}", response_model=list[AgentRead])
async def get_agents_by_tenant(
    tenant_id: uuid.UUID,
    service: AgentService = Depends(get_agent_service),
) -> list[AgentRead]:
    agents = await service.get_by_tenant(tenant_id)
    return [AgentRead.model_validate(a) for a in agents]
