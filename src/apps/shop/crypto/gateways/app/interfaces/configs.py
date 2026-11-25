"""Read and write settings owned by one gateway account."""

from typing import Protocol

from ...domain.dtos.configs import ConfigWrite
from ...domain.results.configs import GatewayConfigView


class IGatewayConfigService(Protocol):
    async def get(self, id: int) -> GatewayConfigView: ...

    async def save(self, id: int, data: ConfigWrite) -> GatewayConfigView: ...


class IGatewayConfigQuery(Protocol):
    async def get(self, id: int) -> GatewayConfigView: ...
