"""Reserve due nodes and check them through the HostService gateway."""

from asyncio import TaskGroup
from datetime import timedelta
from itertools import batched
from math import ceil

from src.apps.network.nodes.observations.app.interfaces.host import (
    INodeHostGateway,
)
from src.apps.network.nodes.observations.domain.enums.host import (
    HostStatsStatus,
)

from ...domain.enums.connection import NodeConnectionStatus
from ...domain.results.probe import (
    NodeProbeBatch,
    NodeProbeClaim,
)
from ..executions.probe import NodeProbeExecution

PROBE_INTERVAL_SECONDS = 10
_BATCH_SIZE = 32
_CONCURRENCY = 5
_PROBE_TIMEOUT = 5

_CONNECTION_STATUSES = {
    HostStatsStatus.AVAILABLE: NodeConnectionStatus.REACHABLE,
    HostStatsStatus.PARTIAL: NodeConnectionStatus.REACHABLE,
    HostStatsStatus.TIMEOUT: NodeConnectionStatus.TIMEOUT,
    HostStatsStatus.UNAVAILABLE: NodeConnectionStatus.UNAVAILABLE,
    HostStatsStatus.REJECTED: NodeConnectionStatus.REJECTED,
    HostStatsStatus.UNSUPPORTED: NodeConnectionStatus.UNSUPPORTED,
}


class NodeProbePipeline:
    def __init__(
        self,
        execution: NodeProbeExecution,
        gateway: INodeHostGateway,
    ) -> None:
        self.execution = execution
        self.gateway = gateway

    async def run(self) -> NodeProbeBatch:
        """Check one bounded batch and count actually committed results."""
        delay = timedelta(seconds=PROBE_INTERVAL_SECONDS)
        rpc_budget = timedelta(
            seconds=ceil(_BATCH_SIZE / _CONCURRENCY) * _PROBE_TIMEOUT
        )
        claims = await self.execution.claim(
            delay=delay,
            reclaim_after=delay + rpc_budget,
            limit=_BATCH_SIZE,
        )
        recorded = 0
        for batch in batched(claims, _CONCURRENCY):
            async with TaskGroup() as group:
                tasks = [
                    group.create_task(self._probe(claim)) for claim in batch
                ]
            recorded += sum(task.result() for task in tasks)
        return NodeProbeBatch(selected=len(claims), recorded=recorded)

    async def _probe(self, claim: NodeProbeClaim) -> bool:
        """Read outside SQL, then record the typed outcome for this claim."""
        target = claim.target
        outcome = await self.gateway.read(
            target, timeout=min(_PROBE_TIMEOUT, target.default_timeout)
        )
        status = _CONNECTION_STATUSES.get(
            outcome.status, NodeConnectionStatus.FAILED
        )
        recorded = await self.execution.complete(claim, status)
        return recorded
