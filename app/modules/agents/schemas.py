"""Pydantic schemas for agents API."""
import uuid

from pydantic import BaseModel, Field

from app.modules.agents.models import AgentNature


class AgentCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=255)
    second_name: str = Field(default="", max_length=255)
    email: str | None = None
    nature: AgentNature = Field(...)


class AgentUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=255)
    second_name: str | None = Field(None, max_length=255)
    email: str | None = None
    nature: AgentNature | None = None


class AgentRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    first_name: str
    second_name: str
    email: str | None
    nature: AgentNature
    origin_id: str | None
    origin_type: str | None

    model_config = {"from_attributes": True}
