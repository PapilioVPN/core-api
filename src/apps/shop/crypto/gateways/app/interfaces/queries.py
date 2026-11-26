"""Read gateway accounts that can be used for payment."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.results.methods import GatewayOption


class IGatewayMethodsQuery(Protocol):
    async def list(
        self, amount: int, *, limit: int, offset: int
    ) -> PagedType[GatewayOption]: ...
