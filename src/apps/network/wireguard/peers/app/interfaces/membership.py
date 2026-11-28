"""Read the effective peer membership of a WireGuard interface."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.membership import WireGuardPeer


class IWireGuardMembershipGateway(Protocol):
    async def read(
        self, node: NodeModel, name: str
    ) -> NodeObservation[tuple[WireGuardPeer, ...]]: ...


class IWireGuardMembershipQuery(Protocol):
    async def get(
        self, node_id: int, name: str
    ) -> NodeObservation[tuple[WireGuardPeer, ...]]: ...
