"""Core dependency providers: db, shared infra only. Wiring only."""

from app.core.database import get_db

__all__ = ["get_db"]
