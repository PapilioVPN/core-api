"""Read one bounded RPC on the registered Node channel."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from re import fullmatch

from grpc import StatusCode
from grpc.aio import AioRpcError, Channel

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from .channels import NodeChannels

_OUTCOMES = {
    StatusCode.NOT_FOUND: NodeReadStatus.TARGET_NOT_FOUND,
    StatusCode.ABORTED: NodeReadStatus.BUSY,
    StatusCode.RESOURCE_EXHAUSTED: NodeReadStatus.RESOURCE_LIMIT,
    StatusCode.FAILED_PRECONDITION: NodeReadStatus.PRECONDITION_FAILED,
    StatusCode.DEADLINE_EXCEEDED: NodeReadStatus.TIMEOUT,
    StatusCode.UNAVAILABLE: NodeReadStatus.UNAVAILABLE,
    StatusCode.INVALID_ARGUMENT: NodeReadStatus.REJECTED,
    StatusCode.UNAUTHENTICATED: NodeReadStatus.REJECTED,
    StatusCode.PERMISSION_DENIED: NodeReadStatus.REJECTED,
    StatusCode.UNIMPLEMENTED: NodeReadStatus.UNSUPPORTED,
}


def valid_config_digest(digest: str) -> bool:
    """Check the lowercase hex digest reported by Node."""
    return fullmatch(r"[a-f0-9]{64}", digest) is not None


async def observe[Reply, Value](
    channels: NodeChannels,
    node: NodeModel,
    call: Callable[[Channel], Awaitable[Reply]],
    decode: Callable[[Reply], Value | None],
) -> NodeObservation[Value]:
    """Call the registered endpoint once and translate its reply.

    Args:
        channels: Application-owned authenticated Node channels.
        node: Materialized registry record with the selected endpoint.
        call: The native unary RPC with its operation-specific deadline.
        decode: Typed reply mapping, returning None for inconsistent evidence.

    Returns:
        An observation or its failure status. Caller cancellation propagates.
    """
    channel = await channels.get(node.endpoint())
    if channel is None:
        result = NodeObservation[Value](NodeReadStatus.NOT_CONFIGURED)
    else:
        try:
            reply = await call(channel)
        except AioRpcError as error:
            status = _OUTCOMES.get(error.code(), NodeReadStatus.FAILED)
            result = NodeObservation[Value](status)
        else:
            received_at = datetime.now(UTC)
            value = decode(reply)
            result = (
                NodeObservation(NodeReadStatus.OBSERVED, value, received_at)
                if value is not None
                else NodeObservation[Value](NodeReadStatus.FAILED)
            )
    return result
