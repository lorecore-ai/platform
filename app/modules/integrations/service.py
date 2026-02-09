import logging
from typing import Type, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.base import BaseIntegration, Action
from app.integrations.registry import IntegrationRegistry
from app.modules.events.service import EventService
from app.modules.secrets.base import SecretsManager

from .models import Integration


logger = logging.getLogger(__name__)


class IntegrationService:
    """
    """

    def __init__(
        self,
        db: AsyncSession,
        registry: IntegrationRegistry,
        secrets: SecretsManager,
        event_service: EventService,
    ):
        self.db = db
        self.registry = registry
        self.secrets = secrets
        self.event_service = event_service

    async def sync(self) -> None:
        logger.info("Syncing integrations...")

        result = await self.db.execute(select(Integration))
        existing = {i.key: i for i in result.scalars().all()}

        for key, cls in self.registry.all().items():

            if key not in existing:
                self.db.add(
                    Integration(
                        key=cls.key,
                        name=cls.name,
                        description=getattr(cls, "description", ""),
                        enabled=True,
                    )
                )
                logger.info("Added integration -> %s", key)

        await self.db.commit()

        logger.info("Sync complete")
    
    async def _build_connector(
        self,
        tenant_id: str,
        key: str,
    ) -> BaseIntegration:

        connector_class = self.registry.get(key)

        credentials = await self.secrets.get(
            tenant_id=tenant_id,
            integration=key,
        )

        return connector_class(**credentials)

    async def execute(
        self,
        tenant_id: str,
        integration_key: str,
        action: Action,
    ) -> Any:
        """
        Execute action of integration for tenant.
        """

        connector = await self._build_connector(
            tenant_id=tenant_id,
            key=integration_key,
        )

        logger.info(
            "tenant=%s integration=%s action=%s",
            tenant_id,
            integration_key,
            action.type,
        )

        return await connector.execute(action)

    async def handle_webhook(
        self,
        tenant_id: str,
        key: str,
        payload: dict,
        event_type: str = "unknown",
    ):

        event = await self.event_service.create(
            tenant_id=tenant_id,
            event_type=event_type,
        )

        connector = await self._build_connector(tenant_id, key)

        await connector.handle_webhook(payload)

        return event
