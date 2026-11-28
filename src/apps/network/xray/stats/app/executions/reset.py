"""Keep durable reset claims and completion outside the Node network call."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.enums.reset import ResetReason, ResetState
from ...domain.results.reset import ResetOutcome, ResetTarget
from ..interfaces.reset import IXrayResetRepository

_DISPATCH_WINDOW = timedelta(seconds=15)


class XrayResetExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    @transactional
    async def claim(
        self,
        id: int,
        *,
        repo: IXrayResetRepository = Inject(),
        nodes: INodeService = Inject(),
    ) -> ResetTarget | None:
        """Reserve the operation once and recheck its registered target."""
        now = utc_now()
        deadline = now + _DISPATCH_WINDOW
        operation = await repo.claim(id, now=now, deadline=deadline)
        target = None
        if operation is not None:
            node = await nodes.get_by_id(operation.node_id)
            if node.is_enabled and (node.address, node.port) == (
                operation.address,
                operation.port,
            ):
                target = ResetTarget(
                    node.endpoint(),
                    operation.instance_id,
                    operation.selection(),
                    deadline,
                )
            else:
                await repo.finish(
                    id,
                    ResetOutcome(
                        ResetState.NOT_APPLIED,
                        ResetReason.TARGET_CHANGED,
                    ),
                    now=utc_now(),
                )
        return target

    @request_scoped
    @transactional
    async def finish(
        self,
        id: int,
        outcome: ResetOutcome,
        *,
        repo: IXrayResetRepository = Inject(),
    ) -> None:
        """Record the evidence only while the claim is current."""
        await repo.finish(id, outcome, now=utc_now())
