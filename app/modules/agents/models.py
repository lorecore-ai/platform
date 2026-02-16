"""Agent ORM model."""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import BaseEntity


class AgentNature(str, enum.Enum):
    """Agent nature: human (user), system (LLM), worker (task LLM)."""

    Human = "human"
    System = "system"
    Worker = "worker"


# Backward compatibility
AgentType = AgentNature


class Agent(BaseEntity):
    __tablename__ = "agents"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    second_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nature: Mapped[AgentNature] = mapped_column(
        Enum(
            AgentNature,
            name="agenttype",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    # External integration: origin_type = "telegram" | "whatsapp" | connector key
    origin_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    origin_type: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    threads: Mapped[list["Thread"]] = relationship(
        "Thread",
        secondary="thread_agents",
        back_populates="agents",
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="agent",
    )

    @property
    def name(self) -> str:
        """Display name: first_name + second_name."""
        return f"{self.first_name} {self.second_name}".strip() or self.first_name
