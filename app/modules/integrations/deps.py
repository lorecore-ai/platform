"""Integrations module dependency providers. Wiring only."""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.integrations.registry import IntegrationRegistry
from app.modules.events.deps import get_event_service
from app.modules.events.service import EventService
from app.modules.integrations.service import IntegrationService
from app.modules.secrets.base import SecretsManager
from app.modules.secrets.deps import get_secrets


def get_registry(request: Request) -> IntegrationRegistry:
    """Integration registry from app state (set in lifespan)."""
    return request.app.state.registry


def get_integration_service(
    db: AsyncSession = Depends(get_db),
    registry: IntegrationRegistry = Depends(get_registry),
    secrets: SecretsManager = Depends(get_secrets),
    event_service: EventService = Depends(get_event_service),
) -> IntegrationService:
    """Request-scoped integration service."""
    return IntegrationService(
        db=db,
        registry=registry,
        secrets=secrets,
        event_service=event_service,
    )
