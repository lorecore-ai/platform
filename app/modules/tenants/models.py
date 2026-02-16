"""Tenant ORM model."""
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import BaseEntity


class Tenant(BaseEntity):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
