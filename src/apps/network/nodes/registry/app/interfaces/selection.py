"""Read bounded choices for the Node picker."""

from typing import Protocol

from ...domain.dtos.records import NodeSelectionInput
from ...domain.results.records import NodeChoice, NodeSelection


class INodeSelectionReader(Protocol):
    async def select_choices(
        self,
        *,
        before_id: int | None,
        limit: int,
        q: str | None,
        is_enabled: bool | None,
    ) -> tuple[NodeChoice, ...]: ...


class INodeSelectionQuery(Protocol):
    async def get(self, data: NodeSelectionInput) -> NodeSelection: ...
