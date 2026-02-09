from typing import Protocol, Dict, Any

class SecretsManager(Protocol):
    async def get(self, tenant_id: str, integration: str) -> Dict[str, Any]:
        pass

    async def set(self, tenant_id: str, integration: str, data: Dict[str, Any]) -> None:
        pass

    async def delete(self, tenant_id: str, integration: str) -> None:
        pass
