"""Pydantic schemas for agents API."""
import uuid

from pydantic import BaseModel, Field

from app.modules.agents.models import AgentType


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: AgentType = Field(...)


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: AgentType | None = None


class AgentRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    name: str
    type: AgentType

    model_config = {"from_attributes": True}
