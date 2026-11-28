"""Read Xray's observed state using the existing Node gRPC transport."""

from datetime import UTC, datetime

from grpc import StatusCode
from grpc.aio import AioRpcError

from src.apps.network.nodes.infra.grpc.channels import NodeChannels

from ...domain.enums.status import XrayStatusCode
from ...domain.results.status import XrayStatusResult
from .codec import decode_instance
from .v1.instances_pb2 import XrayInstanceRequest, XrayInstanceStatus
from .v1.instances_pb2_grpc import XrayInstancesServiceStub

_STATUS_DEADLINE_SECONDS = 3
_RPC_OUTCOMES = {
    StatusCode.NOT_FOUND: XrayStatusCode.INSTANCE_NOT_FOUND,
    StatusCode.DEADLINE_EXCEEDED: XrayStatusCode.TIMEOUT,
    StatusCode.UNAVAILABLE: XrayStatusCode.UNAVAILABLE,
    StatusCode.UNAUTHENTICATED: XrayStatusCode.REJECTED,
    StatusCode.PERMISSION_DENIED: XrayStatusCode.REJECTED,
    StatusCode.UNIMPLEMENTED: XrayStatusCode.UNSUPPORTED,
}


class XrayStatusGateway:
    def __init__(self, channels: NodeChannels) -> None:
        """Borrow the shared channel owner without holding a DB scope."""
        self.channels = channels
        self.stubs: dict[int, XrayInstancesServiceStub] = {}

    async def read(
        self, node_id: int, address: str, port: int, instance_id: str
    ) -> XrayStatusResult:
        """Issue one GetStatus call with a bounded deadline.

        Args:
            node_id: Core identity that owns the management target.
            address: Registered management address.
            port: Registered management port.
            instance_id: Native Xray instance ID.

        Returns:
            A correlated observation or a stable, credential-free outcome.
            Caller cancellation propagates.
        """
        channel = self.channels.get(node_id, address, port)
        if channel is None:
            result = XrayStatusResult(XrayStatusCode.NOT_CONFIGURED)
        else:
            stub = self.stubs.get(node_id)
            if stub is None:
                stub = XrayInstancesServiceStub(channel)
                self.stubs[node_id] = stub
            try:
                reply: XrayInstanceStatus = await stub.GetStatus(
                    XrayInstanceRequest(id=instance_id),
                    timeout=_STATUS_DEADLINE_SECONDS,
                )
            except AioRpcError as error:
                code = _RPC_OUTCOMES.get(error.code(), XrayStatusCode.FAILED)
                result = XrayStatusResult(code)
            else:
                received_at = datetime.now(UTC)
                instance = decode_instance(reply, instance_id)
                result = (
                    XrayStatusResult(
                        XrayStatusCode.OBSERVED, instance, received_at
                    )
                    if instance is not None
                    else XrayStatusResult(XrayStatusCode.FAILED)
                )
        return result
