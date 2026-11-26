"""Start an Xray instance with the configuration selected by Node."""

from grpc import StatusCode
from grpc.aio import AioRpcError
from papilio.utils.dates import utc_now

from src.apps.network.nodes.infra.grpc.channels import NodeChannels

from ...domain.enums.start import XrayStartReason, XrayStartState
from ...domain.enums.status import XrayInstanceState
from ...domain.results.start import XrayStartOutcome, XrayStartTarget
from .codec import decode_instance
from .v1.instances_pb2 import XrayInstanceRequest
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

    async def start(self, target: XrayStartTarget) -> XrayStartOutcome:
        """Dispatch against the captured TLS target and correlate the reply.

        Args:
            target: Registered management target and its dispatch deadline.

        Returns:
            Confirmed evidence, a rejection, or an unconfirmed outcome.
            Caller cancellation propagates.
        """
        remaining = (target.deadline_at - utc_now()).total_seconds()
        channel = self.channels.get(
            target.node_id, target.address, target.port
        )
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
                reply = await stub.Start(
                    XrayInstanceRequest(id=target.instance_id),
                    timeout=min(remaining, _START_DEADLINE_SECONDS),
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
                    and instance.state is XrayInstanceState.READY
                    and instance.applied_config_sha256 is not None
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
