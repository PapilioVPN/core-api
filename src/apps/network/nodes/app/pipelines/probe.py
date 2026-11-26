"""Reserve due nodes and check them through the HostService gateway."""

from asyncio import Semaphore, TaskGroup
from datetime import timedelta
from logging import getLogger
from math import ceil

from ...config import NodeHostConfig
from ...domain.enums.connection import NodeConnectionStatus
from ...domain.enums.host import HostStatsStatus
from ...domain.results.probe import (
    NodeProbeBatch,
    NodeProbeClaim,
    NodeProbeTarget,
)
from ..executions.probe import NodeProbeExecution
from ..interfaces.host import INodeHostGateway

log = getLogger(__name__)

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
        config: NodeHostConfig,
        execution: NodeProbeExecution,
        gateway: INodeHostGateway,
    ) -> None:
        self.config = config
        self.execution = execution
        self.gateway = gateway

    async def run(self) -> NodeProbeBatch:
        """Check one bounded batch and count actually committed results."""
        checks = self.config.checks
        result = NodeProbeBatch(selected=0, recorded=0)
        if self.config.targets and checks.interval_seconds is not None:
            targets = tuple(
                NodeProbeTarget(id, target.address, target.port)
                for id, target in self.config.targets.items()
            )
            delay = timedelta(seconds=checks.interval_seconds)
            batches = ceil(checks.batch_size / checks.concurrency)
            rpc_budget = timedelta(
                seconds=batches * self.config.timeout_seconds
            )
            claims = await self.execution.claim(
                targets,
                delay=delay,
                reclaim_after=delay + rpc_budget,
                limit=checks.batch_size,
            )
            slots = Semaphore(checks.concurrency)
            async with TaskGroup() as group:
                tasks = [
                    group.create_task(self._probe(claim, slots))
                    for claim in claims
                ]
            result = NodeProbeBatch(
                selected=len(claims),
                recorded=sum(task.result() for task in tasks),
            )
        return result

    async def _probe(self, claim: NodeProbeClaim, slots: Semaphore) -> bool:
        target = claim.target
        async with slots:
            try:
                outcome = await self.gateway.read(
                    target.id, target.address, target.port
                )
            except Exception as error:
                log.warning(
                    "Node %s host check raised %s",
                    target.id,
                    type(error).__name__,
                )
                status = NodeConnectionStatus.FAILED
            else:
                status = _CONNECTION_STATUSES.get(
                    outcome.status, NodeConnectionStatus.FAILED
                )
            recorded = await self.execution.complete(claim, status)
        return recorded
