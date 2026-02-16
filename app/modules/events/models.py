"""Event ORM model (Postgres)."""
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import BaseEntity


class Event(BaseEntity):
    __tablename__ = "events"

    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
