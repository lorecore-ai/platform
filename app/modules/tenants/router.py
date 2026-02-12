"""Tenants API router"""
import uuid

from fastapi import APIRouter, Depends, status

from app.modules.agents.deps import get_agent_service
from app.modules.agents.schemas import AgentRead
from app.modules.agents.service import AgentService
from app.modules.tenants.deps import get_tenant_service
from app.modules.tenants.schemas import TenantCreate, TenantRead
from app.modules.tenants.service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/", response_model=list[TenantRead])
async def get_tenants(service: TenantService = Depends(get_tenant_service)) -> list[TenantRead]:
    tenants = await service.get_tenants()
    return [TenantRead.model_validate(t) for t in tenants]


@router.post("/", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
) -> TenantRead:
    tenant = await service.create_tenant(data)
    return TenantRead.model_validate(tenant)


@router.get("/{tenant_id}/agents", response_model=list[AgentRead])
async def get_tenant_agents(
    tenant_id: uuid.UUID,
    service: AgentService = Depends(get_agent_service),
) -> list[AgentRead]:
    """Tenant agents (human) + platform LLM agents available for threads."""
    agents = await service.get_available_for_tenant(tenant_id)
    return [AgentRead.model_validate(a) for a in agents]
