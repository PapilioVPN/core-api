"""Commit the dispatch and completion in short native database scopes."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.xray.revisions.app.interfaces.records import (
    IXrayRevisionService,
)
from src.apps.network.xray.revisions.domain.results.records import (
    XrayRevisionSource,
    XraySourceFailure,
)

from ...domain.enums.start import (
    XrayExecutionAction,
    XrayStartReason,
    XrayStartState,
)
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
        actions: tuple[XrayExecutionAction, ...] = (
            XrayExecutionAction.START,
        ),
        *,
        repo: IXrayStartRepository = Inject(),
        nodes: INodeService = Inject(),
    ) -> XrayStartTarget | None:
        """Reserve the first dispatch and verify the captured Node endpoint.

        Args:
            id: Operation identity from the committed event.
            actions: Lifecycle actions accepted by this worker.
            repo: Request-scoped operation storage.
            nodes: Request-scoped node registry.

        Returns:
            A materialized target for the winning delivery, or None.
        """
        now = utc_now()
        deadline = now + _DISPATCH_WINDOW
        operation = await repo.claim(
            id, now=now, deadline=deadline, actions=actions
        )
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
                    revision_id=operation.revision_id,
                    action=operation.action,
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
    async def load_source(
        self,
        revision_id: int,
        *,
        revisions: IXrayRevisionService = Inject(),
    ) -> XrayRevisionSource | XraySourceFailure:
        """Resolve and materialize the selected source in its own scope.

        Args:
            revision_id: Immutable source selected at admission.
            revisions: Request-scoped revision service with its native UoW.

        Returns:
            Exact original bytes and their verified digest.

        Raises:
            NotFoundException: The selected revision is unavailable.
        """
        source = await revisions.get_source(revision_id)
        return source

    @request_scoped
    @transactional
    async def record_stop(
        self, id: int, *, repo: IXrayStartRepository = Inject()
    ) -> bool:
        """Record stop evidence and confirm the restart still owns dispatch.

        Args:
            id: Claimed restart operation identity.
            repo: Request-scoped operation storage.

        Returns:
            Whether the Start phase can proceed under the active deadline.
        """
        recorded = await repo.record_stop(id, now=utc_now())
        return recorded

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
