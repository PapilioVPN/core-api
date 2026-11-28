"""Authenticated storage encryption for Variza account credentials."""

from typing import Protocol

from pydantic import JsonValue, SecretStr

from ...domain.dtos.configs import VarizaConfig, VarizaLinkConfig
from ...domain.enums.records import GatewayKind
from ...domain.models.configs import ConfigModel


class IGatewayConfigCodec(Protocol):
    def seal(self, data: VarizaConfig) -> dict[str, JsonValue] | None: ...

    def open_link(
        self, config: dict[str, JsonValue]
    ) -> VarizaLinkConfig | None: ...

    def open_webhook(
        self, config: dict[str, JsonValue]
    ) -> SecretStr | None: ...


class IGatewayConfigService(Protocol):
    async def link(self, id: int) -> VarizaLinkConfig | None: ...

    async def webhook(self, id: int) -> SecretStr | None: ...


class IConfigService(Protocol):
    async def find(self, key: GatewayKind) -> ConfigModel | None: ...

    async def create(self, data: ConfigModel) -> ConfigModel: ...

    async def replace(
        self, key: GatewayKind, data: dict[str, JsonValue]
    ) -> ConfigModel: ...
