import hvac
from typing import Dict, Any

from .base import SecretsManager

class VaultSecretsManager(SecretsManager):
    def __init__(
        self,
        url: str,
        token: str,
        mount_point: str = "secret",
        prefix: str = "integrations"
    ):
        self.client = hvac.Client(url=url, token=token)
        self.prefix = prefix
        self.mount_point = mount_point

    async def get(self, tenant_id: str, integration: str) -> Dict[str, Any]:
        path = self._path(tenant_id, integration)
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=self.mount_point
        )
        return response["data"]["data"]

    async def set(self, tenant_id: str, integration: str, data: Dict[str, Any]) -> None:
        path = self._path(tenant_id, integration)
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            mount_point=self.mount_point,
            secret=data
        )

    async def delete(self, tenant_id: str, integration: str) -> None:
        pass

    def _path(self, tenant_id: str, integration: str) -> str:
        return f"{self.prefix}/{tenant_id}/{integration}/"