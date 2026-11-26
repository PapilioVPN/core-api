"""Read and write settings owned by one gateway account."""

from typing import Protocol

from ...domain.dtos.configs import (
    ConfigWrite,
    NowPaymentsConfig,
    PlisioConfig,
    PriceCurrency,
)
from ...domain.models.configs import GatewayConfigModel
from ...domain.results.configs import GatewayConfigView


class IGatewayConfigService(Protocol):
    async def get(self, id: int) -> GatewayConfigView: ...

    async def find(self, id: int) -> GatewayConfigModel | None: ...

    async def plisio_price(self, id: int) -> PriceCurrency: ...

    async def save(self, id: int, data: ConfigWrite) -> GatewayConfigModel: ...


class IGatewayConfigQuery(Protocol):
    async def get(self, id: int) -> GatewayConfigView: ...


class IPlisioConfigQuery(Protocol):
    async def get(self, id: int) -> PlisioConfig: ...


class INowPaymentsConfigQuery(Protocol):
    async def find(self, id: int) -> NowPaymentsConfig | None: ...

    async def get(self, id: int) -> NowPaymentsConfig: ...
