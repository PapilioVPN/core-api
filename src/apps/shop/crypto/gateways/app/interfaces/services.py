"""Operations owned by the gateway account service."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import GatewayCreate, GatewayList, GatewayUpdate
from ...domain.models.records import CryptoGatewayModel


class ICryptoGatewayService(Protocol):
    async def create(self, data: GatewayCreate) -> CryptoGatewayModel: ...

    async def get_by_id(self, id: int) -> CryptoGatewayModel: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CryptoGatewayModel]: ...

    async def list(
        self, query: GatewayList
    ) -> PagedType[CryptoGatewayModel]: ...

    async def update(
        self, id: int, data: GatewayUpdate
    ) -> CryptoGatewayModel: ...

    async def remove(self, id: int) -> CryptoGatewayModel: ...
