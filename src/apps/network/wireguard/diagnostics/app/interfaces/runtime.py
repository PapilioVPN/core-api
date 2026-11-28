"""Typed WireGuardRuntime observation contracts."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.runtime import WireGuardRuntime


class IWireGuardRuntimeGateway(Protocol):
    async def read(
        self, node: NodeModel, name: str
    ) -> NodeObservation[WireGuardRuntime]: ...


class IWireGuardRuntimeQuery(Protocol):
    async def get(
        self, node_id: int, name: str
    ) -> NodeObservation[WireGuardRuntime]: ...
