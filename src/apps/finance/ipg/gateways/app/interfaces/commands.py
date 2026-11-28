"""Panel write operations that prepare gateway credentials."""

from typing import Protocol

from ...domain.dtos.configs import GatewayConfig
from ...domain.dtos.records import GatewayCreate
from ...domain.models.records import GatewayModel


class IGatewayCreateCommand(Protocol):
    async def create(self, data: GatewayCreate) -> GatewayModel: ...


class IGatewayConfigCommand(Protocol):
    async def replace(self, id: int, data: GatewayConfig) -> GatewayModel: ...
