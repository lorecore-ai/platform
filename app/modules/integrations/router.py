from fastapi import APIRouter, Request, Depends

from app.modules.integrations.deps import get_integration_service
from app.modules.integrations.service import IntegrationService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/{integration_key}/{tenant_id}")
async def webhook(
    integration_key: str,
    tenant_id: str,
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
):
    payload = await request.json()
    event = await service.handle_webhook(
        tenant_id=tenant_id,
        key=integration_key,
        payload=payload,
    )
    return {"status": "ok", "event_type": event.event_type}
