"""Pydantic schemas for tenants API."""
import uuid

from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class TenantRead(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}
