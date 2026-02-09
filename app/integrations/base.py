from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.integrations.models import Event, Action
from app.integrations.specs import ActionSpec, EventSpec, SecretSpec


class BaseIntegration(ABC):
    """
    Base contract for any integration.
    """

    # required metadata
    key: ClassVar[str]
    name: ClassVar[str]
    version: ClassVar[str] = "1.0.0"

    # declarations (can be empty)
    actions: ClassVar[list[ActionSpec]] = []
    events: ClassVar[list[EventSpec]] = []
    secrets: ClassVar[list[SecretSpec]] = []

    # -------- public API --------

    @abstractmethod
    async def handle_webhook(self, payload: dict) -> Event:
        ...

    async def execute(self, action: Action) -> Any:
        spec = self.get_action_spec(action.type)

        data = spec.validate(action.payload)

        method = getattr(self, spec.handler)

        return await method(data)

    # -------- helpers --------

    @classmethod
    def get_action_spec(cls, name: str) -> ActionSpec:
        for spec in cls.actions:
            if spec.name == name:
                return spec
        raise ValueError(f"Unknown action: {name}")

    @classmethod
    def validate_action_payload(cls, action: Action):
        spec = cls.get_action_spec(action.type)
        return spec.validate(action.payload)
