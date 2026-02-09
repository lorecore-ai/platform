import logging
import os

from fastapi import FastAPI

from app.modules.secrets.base import SecretsManager
from app.modules.secrets.vault import VaultSecretsManager

logger = logging.getLogger(__name__)


async def init_secrets(app: FastAPI) -> SecretsManager:
    logger.info("Initializing secrets...")

    vault_url = os.getenv("VAULT_URL", "http://vault:8200")
    token = os.getenv("VAULT_TOKEN", "root")

    secrets = VaultSecretsManager(url=vault_url, token=token)
    app.state.secrets = secrets

    logger.info("Secrets initialized")

    return secrets