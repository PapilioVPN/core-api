"""Read the selected registry endpoints once before live host fanout."""

from asyncio import Task, TaskGroup

from src.apps.network.nodes.registry.app.interfaces.endpoints import (
    INodeEndpointQuery,
)

from ...domain.dtos.host import FleetHostStatsInput
from ...domain.enums.host import HostStatsStatus
from ...domain.results.host import FleetHostStatsItem, HostStatsResult
from ..services.fanout import HostStatsFanout


class FleetHostStatsQuery:
    def __init__(
        self, nodes: INodeEndpointQuery, fanout: HostStatsFanout
    ) -> None:
        self.nodes = nodes
        self.fanout = fanout

    async def get(
        self, data: FleetHostStatsInput
    ) -> tuple[FleetHostStatsItem, ...]:
        """Read each distinct enabled node and restore selection order.

        Args:
            data: Up to sixteen requested registry IDs.

        Returns:
            An ordered observation or a reason per entry. Request
            cancellation propagates to its in-flight RPCs.
        """
        ids = tuple(dict.fromkeys(data.node_ids))
        endpoints = await self.nodes.get_endpoints(ids)
        results: dict[int, HostStatsResult] = {}
        pending: dict[int, Task[HostStatsResult]] = {}
        async with TaskGroup() as group:
            for id in ids:
                node = endpoints.get(id)
                if node is None:
                    results[id] = HostStatsResult(
                        HostStatsStatus.NODE_NOT_FOUND
                    )
                elif not node.is_enabled:
                    results[id] = HostStatsResult(HostStatsStatus.DISABLED)
                else:
                    pending[id] = group.create_task(self.fanout.read(node))
        results.update((id, task.result()) for id, task in pending.items())
        return tuple(
            FleetHostStatsItem(id, results[id]) for id in data.node_ids
        )
