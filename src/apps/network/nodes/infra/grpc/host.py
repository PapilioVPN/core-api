"""Call HostService over the registered node's management channel."""

from datetime import UTC, datetime

import grpc
from google.protobuf.empty_pb2 import Empty
from grpc.aio import AioRpcError

from ...config import NodeHostConfig
from ...domain.enums.host import HostStatsStatus
from ...domain.results.host import HostStatsResult
from .channels import NodeChannels
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
    def __init__(self, config: NodeHostConfig, channels: NodeChannels) -> None:
        self.config = config
        self.channels = channels
        self.stubs: dict[int, HostServiceStub] = {}

    async def read(
        self, node_id: int, address: str, port: int
    ) -> HostStatsResult:
        """Read one configured target with a bounded RPC deadline.

        Args:
            node_id: Core identity that owns the configured credential.
            address: Current management address from the registry.
            port: Current management port from the registry.

        Returns:
            The live observation or a stable, credential-free failure result.
            A caller cancellation propagates without conversion to a result.
        """
        channel = self.channels.get(node_id, address, port)
        if channel is None:
            result = HostStatsResult(HostStatsStatus.NOT_CONFIGURED)
        else:
            stub = self.stubs.get(node_id)
            if stub is None:
                stub = HostServiceStub(channel)
                self.stubs[node_id] = stub
            try:
                reply: SystemSnapshot = await stub.GetSystemStats(
                    Empty(), timeout=self.config.timeout_seconds
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
