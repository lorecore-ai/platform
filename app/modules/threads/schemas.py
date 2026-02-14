"""Pydantic schemas for threads API."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.threads.models import Message, MessageRole, Thread


class ThreadCreate(BaseModel):
    """
    DTO for thread creation.

    tenant_id: required — tenant owning the thread
    title: optional — default "New thread"
    metadata: optional — JSON metadata
    """

    tenant_id: uuid.UUID = Field(..., description="Tenant owning the thread")
    title: str = Field(default="New thread", max_length=255)
    metadata_: dict | None = Field(default=None, alias="metadata")

    model_config = {"populate_by_name": True}


class ThreadRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    agent_ids: list[uuid.UUID]
    title: str
    metadata_: dict | None = Field(default=None, serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}

    @classmethod
    def from_thread(cls, thread: Thread) -> "ThreadRead":
        """Build from ORM. Use metadata_ column explicitly (avoids Base.metadata conflict)."""
        return cls(
            id=thread.id,
            tenant_id=thread.tenant_id,
            agent_ids=[a.id for a in (thread.agents or [])],
            title=thread.title,
            metadata_=thread.metadata_,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
        )


class MessageCreate(BaseModel):
    """content: message text, agent_id: agent who sends (author)."""

    content: str = Field(..., min_length=1)
    agent_id: uuid.UUID = Field(..., description="Agent who sends the message")


class MessageRead(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    agent_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_message(cls, message: Message) -> "MessageRead":
        """Build from ORM."""
        return cls(
            id=message.id,
            thread_id=message.thread_id,
            agent_id=message.agent_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
