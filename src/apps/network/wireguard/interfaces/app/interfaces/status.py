"""Typed WireGuard status boundary."""

from typing import Protocol

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.results.status import WireGuardStatus


class IWireGuardStatusGateway(Protocol):
    async def read(
        self, node: NodeModel, target_name: str
    ) -> NodeObservation[WireGuardStatus]: ...


class IWireGuardStatusQuery(Protocol):
    async def get(
        self, node_id: int, target_name: str
    ) -> NodeObservation[WireGuardStatus]: ...
