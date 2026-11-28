"""Panel reads for the gateway configuration."""

from typing import Protocol

from ...domain.enums.records import GatewayKind
from ...domain.models.configs import ConfigModel


class IGatewayConfigQuery(Protocol):
    async def get(self, kind: GatewayKind) -> ConfigModel: ...
