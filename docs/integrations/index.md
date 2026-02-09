# Integrations

Integrations are connectors to external systems (messengers, CRM, email, etc.). They accept incoming webhooks, turn them into platform events, and perform outbound actions on request.

## How it works

- The **registry** (`app.integrations.registry`) scans the `app.integrations.connectors` package at startup and registers all classes that inherit from `BaseIntegration`.
- Each integration implements the contract: **webhook handling** → `Event`, **action execution** via `Action`.
- The **integrations** module in `app/modules/integrations` stores integration configuration in the DB and syncs it with the registry; secrets (tokens, keys) are provided by the **secrets** module.

## Contract: BaseIntegration

An integration class must:

1. Inherit from `app.integrations.base.BaseIntegration`.
2. Define attributes: `name`, `key` (unique identifier in the registry). Attribute `version` is optional (default: `"1.0.0"`).
3. Declare capabilities via class attributes:
   - **`secrets`** — list of `SecretSpec(name, description)` — which secrets the connector needs (e.g. bot token).
   - **`actions`** — list of `ActionSpec(name, description, model, handler)` — outbound actions with a Pydantic model for payload and the name of the method that implements them.
   - **`events`** — list of `EventSpec(name, description)` — event types that this integration can emit.
4. Implement:
   - **`handle_webhook(payload: dict) -> Event`** — parse the incoming webhook and return a unified event (use one of the declared event types).
   - For each action: a method with the name from `ActionSpec.handler`, accepting one argument — the validated instance of `ActionSpec.model`. The base class implements **`execute(action: Action)`** and dispatches to these handlers.

Models:

- **Event**: `type`, `external_id` (optional), `payload` (dict).
- **Action**: `type`, `payload` (dict) — at runtime, `payload` is validated against the action’s Pydantic model and the corresponding handler is called with that model instance.

## Writing your first simple integration

The example below follows the declarative style used by the Telegram connector.

### 1. Connector directory

Create a package under `app/integrations/connectors/` — e.g. `app/integrations/connectors/my_service/`.

### 2. Schemas for actions (optional but recommended)

Define Pydantic models for each action’s payload. File `app/integrations/connectors/my_service/schemas.py`:

```python
from pydantic import BaseModel, Field

class SendReply(BaseModel):
    chat_id: str = Field(description="Chat or channel id")
    text: str = Field(description="Reply text")
```

### 3. API client (optional)

File `app/integrations/connectors/my_service/client.py` — a wrapper over the external service’s HTTP/API (like `TelegramClient`).

### 4. Integration class

File `app/integrations/connectors/my_service/connector.py` (the class must be imported in the package so the registry can find it):

```python
from app.integrations.base import BaseIntegration
from app.integrations.models import Event
from app.integrations.specs import ActionSpec, EventSpec, SecretSpec

from .client import MyServiceClient
from .schemas import SendReply

class MyServiceConnector(BaseIntegration):
    name = "MyService"
    key = "my_service"

    secrets = [
        SecretSpec(name="api_key", description="API key for MyService"),
    ]
    actions = [
        ActionSpec(
            name="send_reply",
            description="Send a reply to a chat",
            model=SendReply,
            handler="send_reply",
        ),
    ]
    events = [
        EventSpec(name="my_service.message.received", description="Incoming message"),
    ]

    def __init__(self, api_key: str):
        self.client = MyServiceClient(api_key)

    async def handle_webhook(self, payload: dict) -> Event:
        msg = payload["message"]
        return Event(
            type="my_service.message.received",
            external_id=str(msg["id"]),
            payload={
                "chat_id": str(msg["chat"]["id"]),
                "text": msg.get("text"),
            },
        )

    async def send_reply(self, data: SendReply):
        return await self.client.send_message(chat_id=data.chat_id, text=data.text)
```

You do **not** implement `execute()`: the base class resolves the action by `action.type`, validates `action.payload` with the action’s model, and calls the handler method (e.g. `send_reply`) with the validated instance.

### 5. Registration

The registry scans `app.integrations.connectors.*` and registers all classes that inherit from `BaseIntegration`. After restarting the application, the integration is available under its `key` (e.g. `my_service`).

### 6. Configuration and secrets

Adding the integration to the DB and binding secrets (e.g. `api_key`) is done via the **integrations** and **secrets** modules. The connector is instantiated with these secrets (e.g. `MyServiceConnector(api_key=...)`).

---

Full reference implementation: `app/integrations/connectors/telegram/` — `connector.py` (declarations + `handle_webhook` + `send_message` handler), `schemas.py` (`SendMessage`), `client.py` (`TelegramClient`).
