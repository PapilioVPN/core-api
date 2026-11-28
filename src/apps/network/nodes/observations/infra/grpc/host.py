"""Call HostService over the registered node's management channel."""

from datetime import UTC, datetime

import grpc
from google.protobuf.empty_pb2 import Empty
from grpc.aio import AioRpcError

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint

from ...domain.enums.host import HostStatsStatus
from ...domain.results.host import HostStatsResult
from .codec import decode_host
from .v1.host_pb2 import SystemSnapshot
from .v1.host_pb2_grpc import HostServiceStub

_RPC_OUTCOMES = {
    grpc.StatusCode.DEADLINE_EXCEEDED: HostStatsStatus.TIMEOUT,
    grpc.StatusCode.UNAVAILABLE: HostStatsStatus.UNAVAILABLE,
    grpc.StatusCode.UNAUTHENTICATED: HostStatsStatus.REJECTED,
    grpc.StatusCode.PERMISSION_DENIED: HostStatsStatus.REJECTED,
    grpc.StatusCode.UNIMPLEMENTED: HostStatsStatus.UNSUPPORTED,
}


class NodeHostGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeEndpoint, *, timeout: int | None = None
    ) -> HostStatsResult:
        """Read one configured target with a bounded RPC deadline.

        Args:
            node: The selected revision of the registered management endpoint.
            timeout: Optional operation-specific deadline in seconds.

        Returns:
            The live observation or a stable, credential-free failure result.
            A caller cancellation propagates without conversion to a result.
        """
        channel = await self.channels.get(node)
        if channel is None:
            result = HostStatsResult(HostStatsStatus.NOT_CONFIGURED)
        else:
            stub = HostServiceStub(channel)
            try:
                reply: SystemSnapshot = await stub.GetSystemStats(
                    Empty(),
                    timeout=timeout
                    if timeout is not None
                    else node.default_timeout,
                )
            except AioRpcError as error:
                status = _RPC_OUTCOMES.get(
                    error.code(), HostStatsStatus.FAILED
                )
                result = HostStatsResult(status)
            else:
                received_at = datetime.now(UTC)
                stats = decode_host(reply)
                status = (
                    HostStatsStatus.PARTIAL
                    if stats.is_partial
                    else HostStatsStatus.AVAILABLE
                )
                result = HostStatsResult(status, stats, received_at)
        return result
