"""Agent ORM model."""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentType(str, enum.Enum):
    """Типы агентов платформы."""

    Human = "human"  # пользователь платформы
    System = "system"  # системный LLM
    Worker = "worker"  # специальная LLM для выполнения задач


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
