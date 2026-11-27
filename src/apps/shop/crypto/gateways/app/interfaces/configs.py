"""Read and write settings owned by one gateway account."""

from typing import Protocol

from ...domain.dtos.configs import (
    ConfigWrite,
    NowPaymentsConfig,
    PlisioConfig,
    PriceCurrency,
)
from ...domain.models.configs import GatewayConfigModel
from ...domain.results.configs import ConfigFailure, GatewayConfigView


class IGatewayConfigService(Protocol):
    async def get(self, id: int) -> GatewayConfigView | ConfigFailure: ...

    async def find(self, id: int) -> GatewayConfigModel | None: ...

    async def plisio_price(self, id: int) -> PriceCurrency | ConfigFailure: ...

    async def save(
        self, id: int, data: ConfigWrite
    ) -> GatewayConfigModel | ConfigFailure: ...


class IGatewayConfigQuery(Protocol):
    async def get(self, id: int) -> GatewayConfigView | ConfigFailure: ...


class IPlisioConfigQuery(Protocol):
    async def get(self, id: int) -> PlisioConfig | ConfigFailure: ...


class INowPaymentsConfigQuery(Protocol):
    async def find(
        self, id: int
    ) -> NowPaymentsConfig | ConfigFailure | None: ...
