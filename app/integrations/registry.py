import pkgutil
import importlib
import logging
from typing import Dict, Type
from app.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)

class IntegrationRegistry:
    """
    """
    def __init__(self):
        self._map: Dict[str, Type[BaseIntegration]] = {}

    def discover(self) -> None:
        import app.integrations.connectors as pkg

        logger.info("Starting integration discovery...")

        count = 0

        for _, module_name, _ in pkgutil.iter_modules(pkg.__path__):
            module = importlib.import_module(
                f"{pkg.__name__}.{module_name}"
            )

            for obj in module.__dict__.values():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, BaseIntegration)
                    and obj is not BaseIntegration
                ):
                    self._register(obj)
                    count += 1

        logger.info("Integration discovery finished. Loaded=%s", count)

    def _register(self, cls: Type[BaseIntegration]) -> None:
        key = cls.key

        if not key:
            logger.warning(
                "Skipping integration without key: %s",
                cls.__name__,
            )
            return

        if key in self._map:
            logger.warning(
                "Duplicate integration key '%s'. Overriding %s with %s",
                key,
                self._map[key].__name__,
                cls.__name__,
            )

        self._map[key] = cls

        logger.info(
            "Registered integration: key=%s class=%s",
            key,
            cls.__name__,
        )

    def get(self, key: str) -> Type[BaseIntegration]:
        if key not in self._map:
            raise KeyError(f"Integration '{key}' not registered")
        return self._map[key]

    def all(self) -> Dict[str, Type[BaseIntegration]]:
        return self._map