"""Pydantic schemas for threads API."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.threads.models import MessageRole


class ThreadCreate(BaseModel):
    agent_id: uuid.UUID = Field(...)
    title: str = Field(default="New thread", max_length=255)


class ThreadRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    agent_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageRead(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
