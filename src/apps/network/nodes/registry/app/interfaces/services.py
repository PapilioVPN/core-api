"""Node registration operations used by the administrator panel."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import NodeCreate, NodeList, NodeUpdate
from ...domain.models.records import NodeModel


class INodeService(Protocol):
    async def create(self, data: NodeCreate) -> NodeModel: ...

    async def get_by_id(self, id: int) -> NodeModel: ...

    async def list(self, query: NodeList) -> PagedType[NodeModel]: ...

    async def update(self, id: int, data: NodeUpdate) -> NodeModel: ...
