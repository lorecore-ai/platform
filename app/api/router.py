from fastapi import APIRouter

from app.modules.agents import router as agents_router
from app.modules.integrations import router as integrations_router
from app.modules.tenants import router as tenants_router
from app.modules.threads import router as threads_router

api_router = APIRouter(prefix="/api")

api_router.include_router(agents_router)
api_router.include_router(integrations_router)
api_router.include_router(tenants_router)
api_router.include_router(threads_router)
