"""Agents API router."""
import uuid

from fastapi import APIRouter, Depends

from app.modules.agents.deps import get_agent_service
from app.modules.agents.schemas import AgentRead
from app.modules.agents.service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/tenant/{tenant_id}", response_model=list[AgentRead])
async def get_agents_by_tenant(
    tenant_id: uuid.UUID,
    service: AgentService = Depends(get_agent_service),
) -> list[AgentRead]:
    agents = await service.get_by_tenant(tenant_id)
    return [AgentRead.model_validate(a) for a in agents]
