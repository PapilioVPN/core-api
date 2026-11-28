"""Compare desired revisions for a bounded selection after finishing SQL."""

from asyncio import Task, TaskGroup

from papilio.infra.db.tools.decorators import transactional

from src.apps.network.nodes.app.interfaces.endpoints import INodeEndpointQuery
from src.apps.network.nodes.domain.results.records import NodeEndpoint
from src.apps.network.xray.instances.app.interfaces.status import (
    IXrayStatusFanout,
)
from src.apps.network.xray.instances.domain.dtos.identity import (
    XrayExecutionKey,
)
from src.apps.network.xray.instances.domain.enums.status import XrayStatusCode
from src.apps.network.xray.instances.domain.results.status import (
    XrayStatusResult,
)

from ...domain.dtos.fleet_comparison import XrayFleetComparisonInput
from ...domain.results.records import (
    XrayDesiredRevision,
    XrayFleetComparisonItem,
)
from ..interfaces.fleet_comparison import IXrayAssignmentReader
from ..policies.comparison import build_comparison


class XrayFleetComparisonQuery:
    def __init__(
        self,
        nodes: INodeEndpointQuery,
        assignments: IXrayAssignmentReader,
        fanout: IXrayStatusFanout,
    ) -> None:
        self.nodes = nodes
        self.assignments = assignments
        self.fanout = fanout

    async def get(
        self, data: XrayFleetComparisonInput
    ) -> tuple[XrayFleetComparisonItem, ...]:
        """Compare distinct assigned targets and reproduce the input order.

        Args:
            data: Up to sixteen validated Node and instance pairs.

        Returns:
            One verdict per row, retaining missing and unavailable evidence.
            Client cancellation propagates to the in-flight observations.
        """
        order = [
            (target.node_id, target.instance_id) for target in data.targets
        ]
        keys = tuple(dict.fromkeys(order))
        endpoints, desired = await self._select(keys)
        observed: dict[XrayExecutionKey, XrayStatusResult] = {}
        pending: dict[XrayExecutionKey, Task[XrayStatusResult]] = {}
        async with TaskGroup() as group:
            for key in keys:
                node_id, instance_id = key
                endpoint = endpoints.get(node_id)
                if endpoint is None:
                    observed[key] = XrayStatusResult(
                        XrayStatusCode.NODE_NOT_FOUND
                    )
                elif key in desired:
                    if endpoint.is_enabled:
                        pending[key] = group.create_task(
                            self.fanout.read(endpoint, instance_id)
                        )
                    else:
                        observed[key] = XrayStatusResult(
                            XrayStatusCode.DISABLED
                        )
        observed.update((key, task.result()) for key, task in pending.items())
        results = {
            key: build_comparison(desired.get(key), observed.get(key))
            for key in keys
        }
        return tuple(
            XrayFleetComparisonItem(*key, results[key]) for key in order
        )

    @transactional
    async def _select(
        self, keys: tuple[XrayExecutionKey, ...]
    ) -> tuple[
        dict[int, NodeEndpoint], dict[XrayExecutionKey, XrayDesiredRevision]
    ]:
        """Materialize local facts before scheduling any remote observation."""
        ids = tuple(dict.fromkeys(node_id for node_id, _ in keys))
        endpoints = await self.nodes.get_endpoints(ids)
        selected = tuple(key for key in keys if key[0] in endpoints)
        desired = (
            await self.assignments.select_desired(selected) if selected else {}
        )
        return endpoints, desired
