"""Record operations for hosted card gateway accounts."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import GatewayList, GatewayUpdate
from ...domain.enums.records import GatewayKind
from ...domain.models.records import GatewayModel


class IGatewayService(Protocol):
    async def create(self, data: GatewayModel) -> GatewayModel: ...

    async def get_by_id(self, id: int) -> GatewayModel: ...

    async def find_by_id(self, id: int) -> GatewayModel | None: ...

    async def find_by_kind(self, kind: GatewayKind) -> GatewayModel | None: ...

    async def list(self, query: GatewayList) -> PagedType[GatewayModel]: ...

    async def update(self, id: int, data: GatewayUpdate) -> GatewayModel: ...
