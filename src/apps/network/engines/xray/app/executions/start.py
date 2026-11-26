"""Commit the dispatch and completion in short native database scopes."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now

from src.apps.network.nodes.app.interfaces.services import INodeService

from ...domain.enums.start import XrayStartReason, XrayStartState
from ...domain.results.start import XrayStartOutcome, XrayStartTarget
from ..interfaces.start import IXrayStartRepository

_DISPATCH_WINDOW = timedelta(seconds=45)


class XrayStartExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    @transactional
    async def claim(
        self,
        id: int,
        *,
        repo: IXrayStartRepository = Inject(),
        nodes: INodeService = Inject(),
    ) -> XrayStartTarget | None:
        """Reserve the first dispatch and verify the captured Node endpoint.

        Args:
            id: Operation identity from the committed event.
            repo: Request-scoped operation storage.
            nodes: Request-scoped node registry.

        Returns:
            A materialized target for the winning delivery, or None.
        """
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
                target = XrayStartTarget(
                    operation.node_id,
                    operation.instance_id,
                    operation.address,
                    operation.port,
                    deadline,
                )
            else:
                await repo.finish(
                    id,
                    XrayStartOutcome(
                        XrayStartState.FAILED, XrayStartReason.TARGET_CHANGED
                    ),
                    now=utc_now(),
                )
        return target

    @request_scoped
    @transactional
    async def finish(
        self,
        id: int,
        outcome: XrayStartOutcome,
        *,
        repo: IXrayStartRepository = Inject(),
    ) -> None:
        """Persist the observed result if the dispatch is still active.

        Args:
            id: Operation identity that owns the dispatch.
            outcome: Evidence from the Node call.
            repo: Request-scoped operation storage.
        """
        await repo.finish(id, outcome, now=utc_now())
