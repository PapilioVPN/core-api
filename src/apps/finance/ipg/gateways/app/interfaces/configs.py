"""Protect merchant credentials before handing them to the record service."""

from typing import Protocol

from pydantic import JsonValue, SecretStr

from ...domain.dtos.configs import GatewayConfig
from ...domain.enums.records import GatewayKind
from ...domain.models.configs import ConfigModel
from ...domain.results.configs import Merchant


class IGatewayConfigCodec(Protocol):
    def seal(self, data: GatewayConfig) -> dict[str, JsonValue] | None: ...

    def open(self, config: dict[str, JsonValue]) -> SecretStr | None: ...


class IGatewayConfigService(Protocol):
    async def merchant(self, kind: GatewayKind) -> Merchant | None: ...


class IConfigService(Protocol):
    async def find(self, key: GatewayKind) -> ConfigModel | None: ...

    async def create(self, data: ConfigModel) -> ConfigModel: ...

    async def replace(
        self, key: GatewayKind, data: dict[str, JsonValue]
    ) -> ConfigModel: ...
