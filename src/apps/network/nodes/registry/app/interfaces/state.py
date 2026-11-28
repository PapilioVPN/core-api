"""Typed contract for changing a selection of registered Nodes."""

from typing import Protocol

from ...domain.dtos.records import NodeStateInput
from ...domain.results.records import NodeStateResult


class INodeStateCommand(Protocol):
    async def set_enabled(
        self, data: NodeStateInput
    ) -> tuple[NodeStateResult, ...]: ...
