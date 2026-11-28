"""Cache the encrypted provider configurations."""

from typing import Protocol

from ...domain.enums.records import GatewayKind
from ...domain.models.configs import ConfigModel


class IGatewayConfigCache(Protocol):
    async def find(self, key: GatewayKind) -> ConfigModel | None: ...

    async def store(
        self, key: GatewayKind, record: ConfigModel, ttl: int
    ) -> None: ...

    async def forget(self, key: GatewayKind) -> None: ...


class ICacheOwner(Protocol):
    @property
    def cache(self) -> IGatewayConfigCache: ...
