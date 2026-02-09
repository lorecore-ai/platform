"""Bootstrap: create long-lived registry and run one-off sync. Uses session_context (no direct async_session_factory)."""

import logging

from fastapi import FastAPI

from app.core.database import session_context
from app.modules.events.service import EventService
from app.modules.integrations.service import IntegrationService
from app.modules.secrets.base import SecretsManager

from .registry import IntegrationRegistry

logger = logging.getLogger(__name__)


async def init_integrations(app: FastAPI, secrets: SecretsManager) -> None:
    """Create registry (stored in app.state), then run sync using session_context."""
    logger.info("Initializing integrations...")

    registry = IntegrationRegistry()
    registry.discover()
    app.state.registry = registry

    async with session_context() as db:
        event_service = EventService(db)
        service = IntegrationService(db, registry, secrets, event_service)
        await service.sync()

    logger.info("Integrations initialized")
