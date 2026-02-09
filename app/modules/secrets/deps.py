"""Secrets module dependency providers. Wiring only."""

from fastapi import Request

from app.modules.secrets.base import SecretsManager


def get_secrets(request: Request) -> SecretsManager:
    """Secrets manager from app state (set in lifespan)."""
    return request.app.state.secrets
