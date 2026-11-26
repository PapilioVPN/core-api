"""Contracts for observing the host of a registered node."""

from typing import Protocol

from ...domain.results.host import HostStatsResult


class INodeHostGateway(Protocol):
    async def read(
        self, node_id: int, address: str, port: int
    ) -> HostStatsResult: ...


class IHostStatsQuery(Protocol):
    async def get(self, node_id: int) -> HostStatsResult: ...
