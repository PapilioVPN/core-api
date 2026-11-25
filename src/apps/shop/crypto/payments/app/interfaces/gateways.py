"""Authenticated invoice operations offered by Plisio."""

from typing import Protocol

from src.apps.shop.crypto.gateways.domain.dtos.configs import PlisioConfig

from ...domain.results.check import Operation
from ...domain.results.invoice import Invoice, PlisioIssue


class IPlisioGateway(Protocol):
    async def issue(self, data: PlisioIssue) -> Invoice: ...

    async def read(self, config: PlisioConfig, id: str) -> Operation: ...
