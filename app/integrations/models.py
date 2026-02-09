from pydantic import BaseModel, Field
from typing import Dict, Any

class Event(BaseModel):
    type: str = Field(..., description="Event type")

    external_id: str | None = Field(
        default=None,
        description="The external ID of the event"
    )

    payload: Dict[str, Any]

class Action(BaseModel):
    type: str = Field(..., description="Action type")

    payload: Dict[str, Any]