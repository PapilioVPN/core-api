"""Bind short native request scopes for scheduled node probes."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped

from ...domain.enums.connection import NodeConnectionStatus
from ...domain.results.probe import NodeProbeClaim, NodeProbeTarget
from ..interfaces.probe import INodeProbeRepository


class NodeProbeExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    @transactional
    async def claim(
        self,
        targets: tuple[NodeProbeTarget, ...],
        *,
        delay: timedelta,
        reclaim_after: timedelta,
        limit: int,
        repo: INodeProbeRepository = Inject(),
    ) -> tuple[NodeProbeClaim, ...]:
        """Commit a bounded reservation before any remote service is called."""
        claims = await repo.claim(
            targets, delay=delay, reclaim_after=reclaim_after, limit=limit
        )
        return claims

    @request_scoped
    @transactional
    async def complete(
        self,
        claim: NodeProbeClaim,
        status: NodeConnectionStatus,
        *,
        repo: INodeProbeRepository = Inject(),
    ) -> bool:
        """Commit one result if its reservation still owns the node."""
        recorded = await repo.complete(claim, status)
        return recorded
