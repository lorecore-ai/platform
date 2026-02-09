"""Event service — insert events into Postgres."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .models import Event


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        tenant_id: str,
        integration_id: uuid.UUID,
        event_type: str,
    ) -> Event:
        event = Event(
            tenant_id=tenant_id,
            integration_id=integration_id,
            event_type=event_type,
        )
        self.db.add(event)
        await self.db.flush()
        return event
