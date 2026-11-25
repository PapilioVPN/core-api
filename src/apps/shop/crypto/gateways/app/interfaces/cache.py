"""Cache contract for the safe gateway settings projection."""

from typing import Protocol

from ...domain.results.configs import GatewayConfigView


class IGatewayConfigCache(Protocol):
    async def find(self, id: int) -> GatewayConfigView | None: ...

    async def store(self, view: GatewayConfigView, ttl: int) -> None: ...

    async def forget(self, id: int) -> None: ...


class IGatewayConfigCacheOwner(Protocol):
    @property
    def cache(self) -> IGatewayConfigCache: ...
