"""Event module dependency providers. Wiring only."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.modules.events.service import EventService


def get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
    """Request-scoped event service."""
    return EventService(db)
