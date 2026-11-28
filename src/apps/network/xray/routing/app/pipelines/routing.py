"""Dispatch a routing mutation only after its claim is committed."""

from ...domain.enums.operation import (
    RoutingFailure,
    RoutingPayloadFailure,
    RoutingState,
)
from ...domain.results.operation import RoutingOutcome
from ..executions.routing import XrayRoutingExecution
from ..interfaces.operations import IRoutingPayloadCodec, IXrayRoutingGateway


class XrayRoutingPipeline:
    def __init__(
        self,
        execution: XrayRoutingExecution,
        codec: IRoutingPayloadCodec,
        gateway: IXrayRoutingGateway,
    ) -> None:
        self.execution = execution
        self.codec = codec
        self.gateway = gateway

    async def run(self, id: int) -> None:
        """Dispatch the operator's exact intent under its stored identity.

        Args:
            id: Stable identity from the committed routing request.
        """
        target = await self.execution.claim(id)
        if target is not None:
            intent = await self.codec.open(target.payload)
            if (
                isinstance(intent, RoutingPayloadFailure)
                or intent.action != target.action
            ):
                outcome = RoutingOutcome(
                    RoutingState.FAILED, RoutingFailure.PAYLOAD_UNAVAILABLE
                )
            else:
                outcome = await self.gateway.mutate(target, intent)
            await self.execution.finish(id, outcome)
