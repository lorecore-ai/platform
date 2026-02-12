"""Pydantic schemas for agents API."""
import uuid

from pydantic import BaseModel, Field

from app.modules.agents.models import AgentType


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: AgentType = Field(...)
    model: str = Field(..., max_length=255)
    system_prompt: str = Field(default="")


class AgentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: AgentType | None = None
    model: str | None = Field(None, max_length=255)
    system_prompt: str | None = None


class AgentRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    type: AgentType
    model: str
    system_prompt: str

    model_config = {"from_attributes": True}
