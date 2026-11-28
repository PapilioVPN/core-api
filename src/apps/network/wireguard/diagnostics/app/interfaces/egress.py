"""Typed WireGuardEgress observation contracts."""

from typing import Protocol

from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.egress import WireGuardEgress


class IWireGuardEgressGateway(Protocol):
    async def read(
        self, node: NodeModel, name: str
    ) -> NodeObservation[WireGuardEgress]: ...


class IWireGuardEgressQuery(Protocol):
    async def get(
        self, node_id: int, name: str
    ) -> NodeObservation[WireGuardEgress]: ...
