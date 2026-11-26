"""Persistence contract for scheduled connection probes."""

from datetime import timedelta
from typing import Protocol

from ...domain.enums.connection import NodeConnectionStatus
from ...domain.results.probe import NodeProbeClaim, NodeProbeTarget


class INodeProbeRepository(Protocol):
    async def claim(
        self,
        targets: tuple[NodeProbeTarget, ...],
        *,
        delay: timedelta,
        reclaim_after: timedelta,
        limit: int,
    ) -> tuple[NodeProbeClaim, ...]: ...

    async def complete(
        self, claim: NodeProbeClaim, status: NodeConnectionStatus
    ) -> bool: ...
