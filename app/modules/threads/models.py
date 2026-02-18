"""Thread and Message ORM models."""
import enum
import uuid

import sqlalchemy as sa
from sqlalchemy import Enum, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, BaseEntity


# Many-to-many: threads <-> agents (conversation participants)
thread_agents = Table(
    "thread_agents",
    Base.metadata,
    sa.Column("thread_id", UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("agent_id", UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
)


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class Thread(BaseEntity):
    __tablename__ = "threads"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New thread")
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        secondary=thread_agents,
        back_populates="threads",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="thread",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
    )

    @property
    def agent_ids(self) -> list[uuid.UUID]:
        """For ThreadRead serialization. Requires agents to be loaded."""
        return [a.id for a in self.agents] if self.agents else []


class Message(BaseEntity):
    __tablename__ = "messages"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    thread: Mapped["Thread"] = relationship("Thread", back_populates="messages")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="messages")
