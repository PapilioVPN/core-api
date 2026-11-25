"""Owning read, write and connection contracts for gateway configuration."""

from typing import Protocol

from ...domain.dtos.configs import ConfigWrite
from ...domain.models.records import CryptoGatewayModel
from ...domain.results.configs import GatewayConfigView


class ICryptoGatewayConfigService(Protocol):
    async def get(self, id: int) -> GatewayConfigView: ...

    async def save(self, id: int, data: ConfigWrite) -> GatewayConfigView: ...

    async def connection(self, gateway: CryptoGatewayModel) -> ConfigWrite: ...


class ICryptoGatewayConfigQuery(Protocol):
    async def get(self, id: int) -> GatewayConfigView: ...
