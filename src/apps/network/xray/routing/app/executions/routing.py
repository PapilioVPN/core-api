"""Use separate Papilio request scopes for routing claim and result."""

from datetime import timedelta

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped
from papilio.utils.dates import utc_now

from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.enums.operation import RoutingFailure, RoutingState
from ...domain.results.operation import (
    RoutingOutcome,
    RoutingPayload,
    RoutingTarget,
)
from ..interfaces.operations import IXrayRoutingOperationRepository

_DISPATCH_WINDOW = timedelta(seconds=15)


class XrayRoutingExecution:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    @request_scoped
    @transactional
    async def claim(
        self,
        id: int,
        *,
        repo: IXrayRoutingOperationRepository = Inject(),
        nodes: INodeService = Inject(),
    ) -> RoutingTarget | None:
        """Claim once and check the registered endpoint before dispatch.

        Args:
            id: Identity of the committed operation to claim.
            repo: Request-scoped operation storage.
            nodes: Request-scoped Node registry.

        Returns:
            The captured Node and encrypted input for the winning claim.
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
                target = RoutingTarget(
                    node.endpoint(),
                    operation.instance_id,
                    operation.action,
                    deadline,
                    RoutingPayload(
                        operation.payload_digest, operation.ciphertext
                    ),
                )
            else:
                await repo.finish(
                    id,
                    RoutingOutcome(
                        RoutingState.FAILED, RoutingFailure.TARGET_CHANGED
                    ),
                    now=utc_now(),
                )
        return target

    @request_scoped
    @transactional
    async def finish(
        self,
        id: int,
        outcome: RoutingOutcome,
        *,
        repo: IXrayRoutingOperationRepository = Inject(),
    ) -> None:
        """Record the native acknowledgement or typed failure.

        Args:
            id: Claimed operation identity.
            outcome: Delivery evidence returned by the worker.
            repo: Request-scoped operation storage.
        """
        await repo.finish(id, outcome, now=utc_now())
