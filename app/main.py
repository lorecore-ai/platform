import logging

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.api.router import api_router
from app.core.database import close_db, init_db
from app.integrations.bootstrap import init_integrations
from app.integrations.models import Action
from app.modules.integrations.deps import get_integration_service
from app.modules.secrets.deps import get_secrets
from app.modules.integrations.service import IntegrationService
from app.modules.secrets.base import SecretsManager
from app.modules.secrets.bootstrap import init_secrets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    secrets = await init_secrets(app)
    await init_integrations(app, secrets)
    yield
    await close_db()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)


@app.get("/")
async def root(
    service: IntegrationService = Depends(get_integration_service),
    secrets: SecretsManager = Depends(get_secrets),
):
    return {"message": "Hello, World!"}
