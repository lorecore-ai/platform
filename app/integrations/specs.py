from typing import Type, Any
from pydantic import BaseModel


class ActionSpec(BaseModel):
    name: str
    description: str
    model: Type[BaseModel]
    handler: str

    def validate(self, payload: dict) -> BaseModel:
        return self.model(**payload)

    @property
    def schema(self) -> dict:
        return self.model.model_json_schema()


class EventSpec(BaseModel):
    name: str
    description: str


class SecretSpec(BaseModel):
    name: str
    description: str
    required: bool = True
