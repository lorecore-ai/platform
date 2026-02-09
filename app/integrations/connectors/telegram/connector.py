from typing import Any

from app.integrations.base import BaseIntegration
from app.integrations.models import Action, Event
from app.integrations.specs import ActionSpec, EventSpec, SecretSpec

from .client import TelegramClient
from .schemas import SendMessage


class TelegramConnector(BaseIntegration):
    name = "Telegram"
    key = "telegram"

    # ---------------------------
    # Declarations
    # ---------------------------

    secrets = [
        SecretSpec(
            name="token",
            description="Telegram bot token",
        )
    ]

    actions = [
        ActionSpec(
            name="send_message",
            description="Send text message to chat",
            model=SendMessage,
            handler="send_message",
        )
    ]

    events = [
        EventSpec(
            name="telegram.message.received",
            description="Incoming message",
        )
    ]

    # ---------------------------

    def __init__(self, token: str):
        self.client = TelegramClient(token)

    # ---------------------------

    async def handle_webhook(self, payload: dict) -> Event:
        message = payload["message"]

        return Event(
            type="telegram.message.received",
            external_id=str(message["message_id"]),
            payload={
                "chat_id": str(message["chat"]["id"]),
                "user_id": str(message["from"]["id"]),
                "text": message.get("text"),
            },
        )

    async def send_message(self, data: SendMessage):
        return await self.client.send_message(
            chat_id=data.chat_id,
            text=data.text,
        )