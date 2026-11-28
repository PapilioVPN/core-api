"""Correlate one registry snapshot and a bounded set of live Xray reads."""

from asyncio import Task, TaskGroup

from src.apps.network.nodes.registry.app.interfaces.endpoints import (
    INodeEndpointQuery,
)

from ...domain.dtos.fleet_status import XrayFleetStatusInput
from ...domain.enums.status import XrayStatusCode
from ...domain.results.status import XrayFleetStatusItem, XrayStatusResult
from ..interfaces.status import IXrayStatusFanout


class XrayFleetStatusQuery:
    def __init__(
        self, nodes: INodeEndpointQuery, fanout: IXrayStatusFanout
    ) -> None:
        self.nodes = nodes
        self.fanout = fanout

    async def get(
        self, data: XrayFleetStatusInput
    ) -> tuple[XrayFleetStatusItem, ...]:
        """Keep input order and read each distinct target once."""
        order = [
            (target.node_id, target.instance_id) for target in data.targets
        ]
        ids = tuple(dict.fromkeys(node_id for node_id, _ in order))
        endpoints = await self.nodes.get_endpoints(ids)
        results: dict[tuple[int, str], XrayStatusResult] = {}
        pending: dict[tuple[int, str], Task[XrayStatusResult]] = {}
        async with TaskGroup() as group:
            for key in dict.fromkeys(order):
                node_id, instance_id = key
                endpoint = endpoints.get(node_id)
                if endpoint is None:
                    results[key] = XrayStatusResult(
                        XrayStatusCode.NODE_NOT_FOUND
                    )
                elif not endpoint.is_enabled:
                    results[key] = XrayStatusResult(XrayStatusCode.DISABLED)
                else:
                    pending[key] = group.create_task(
                        self.fanout.read(endpoint, instance_id)
                    )
        results.update((key, task.result()) for key, task in pending.items())
        return tuple(XrayFleetStatusItem(*key, results[key]) for key in order)
