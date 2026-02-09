from pydantic import BaseModel, Field


class SendMessage(BaseModel):
    chat_id: str = Field(description="Telegram chat id")
    text: str = Field(description="Message text")
