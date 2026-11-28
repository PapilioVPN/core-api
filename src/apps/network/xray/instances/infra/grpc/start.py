"""Start an Xray instance through the versioned Node contract."""

from collections.abc import Awaitable, Callable

from grpc import StatusCode
from grpc.aio import AioRpcError
from papilio.utils.dates import utc_now

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels

from ...domain.enums.start import XrayStartReason, XrayStartState
from ...domain.enums.status import XrayInstanceState
from ...domain.results.start import XrayStartOutcome, XrayStartTarget
from .codec import decode_instance
from .v1.instances_pb2 import XrayInstanceRequest, XrayInstanceStatus
from .v1.instances_pb2_grpc import XrayInstancesServiceStub

_START_DEADLINE_SECONDS = 20
_FAILED = {
    StatusCode.NOT_FOUND: XrayStartReason.INSTANCE_NOT_FOUND,
    StatusCode.INVALID_ARGUMENT: XrayStartReason.REJECTED,
    StatusCode.UNAUTHENTICATED: XrayStartReason.REJECTED,
    StatusCode.PERMISSION_DENIED: XrayStartReason.REJECTED,
    StatusCode.UNIMPLEMENTED: XrayStartReason.UNSUPPORTED,
    StatusCode.ABORTED: XrayStartReason.BUSY,
}
_UNKNOWN = {
    StatusCode.DEADLINE_EXCEEDED: XrayStartReason.TIMEOUT,
    StatusCode.UNAVAILABLE: XrayStartReason.UNAVAILABLE,
}


class XrayStartGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def start(
        self, target: XrayStartTarget, config_json: bytes | None = None
    ) -> XrayStartOutcome:
        """Dispatch against the captured TLS target and correlate the reply.

        Args:
            target: Registered management target and its dispatch deadline.
            config_json: Exact revision bytes, or None for the Node-local file.

        Returns:
            Confirmed evidence, a rejection, or an unconfirmed outcome.
            Caller cancellation propagates.
        """
        request = XrayInstanceRequest(
            id=target.instance_id, config_json=config_json
        )
        outcome = await self._execute(
            target,
            lambda stub, timeout: stub.Start(request, timeout=timeout),
            XrayInstanceState.READY,
        )
        return outcome

    async def stop(self, target: XrayStartTarget) -> XrayStartOutcome:
        """Stop a selected execution using its bounded dispatch window.

        Args:
            target: Registered management target and its dispatch deadline.

        Returns:
            Confirmed Stop evidence or a typed failure outcome.
        """
        request = XrayInstanceRequest(id=target.instance_id)
        outcome = await self._execute(
            target,
            lambda stub, timeout: stub.Stop(request, timeout=timeout),
            XrayInstanceState.STOPPED,
        )
        return outcome

    async def _execute(
        self,
        target: XrayStartTarget,
        call: Callable[
            [XrayInstancesServiceStub, float], Awaitable[XrayInstanceStatus]
        ],
        expected: XrayInstanceState,
    ) -> XrayStartOutcome:
        channel = await self.channels.get(target.node)
        remaining = (target.deadline_at - utc_now()).total_seconds()
        if remaining <= 0:
            outcome = XrayStartOutcome(
                XrayStartState.UNKNOWN, XrayStartReason.DISPATCH_EXPIRED
            )
        elif channel is None:
            outcome = XrayStartOutcome(
                XrayStartState.FAILED, XrayStartReason.NOT_CONFIGURED
            )
        else:
            stub = XrayInstancesServiceStub(channel)
            try:
                reply = await call(
                    stub, min(remaining, _START_DEADLINE_SECONDS)
                )
            except AioRpcError as error:
                code = error.code()
                reason = _FAILED.get(code)
                outcome = (
                    XrayStartOutcome(XrayStartState.FAILED, reason)
                    if reason is not None
                    else XrayStartOutcome(
                        XrayStartState.UNKNOWN,
                        _UNKNOWN.get(code, XrayStartReason.UNCONFIRMED),
                    )
                )
            else:
                instance = decode_instance(reply, target.instance_id)
                if (
                    instance is not None
                    and instance.state is expected
                    and (
                        expected is XrayInstanceState.STOPPED
                        or instance.applied_config_sha256 is not None
                    )
                ):
                    outcome = XrayStartOutcome(
                        XrayStartState.SUCCEEDED,
                        applied_config_sha256=instance.applied_config_sha256,
                    )
                else:
                    outcome = XrayStartOutcome(
                        XrayStartState.UNKNOWN, XrayStartReason.UNCONFIRMED
                    )
        return outcome
