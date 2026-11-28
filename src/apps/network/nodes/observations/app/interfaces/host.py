"""Contracts for observing the host of a registered node."""

from typing import Protocol

from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint

from ...domain.dtos.host import FleetHostStatsInput
from ...domain.results.host import FleetHostStatsItem, HostStatsResult


class INodeHostGateway(Protocol):
    async def read(
        self, node: NodeEndpoint, *, timeout: int | None = None
    ) -> HostStatsResult: ...


class IHostStatsQuery(Protocol):
    async def get(self, node_id: int) -> HostStatsResult: ...


class IFleetHostStatsQuery(Protocol):
    async def get(
        self, data: FleetHostStatsInput
    ) -> tuple[FleetHostStatsItem, ...]: ...
