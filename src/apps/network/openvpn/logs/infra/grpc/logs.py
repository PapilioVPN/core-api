"""Follow the pinned OpenVPN log RPC on the shared Node channel."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial

from src.apps.network.nodes.connections.infra.grpc.streams import (
    NodeLogStreams,
)
from src.apps.network.nodes.observations.domain.enums.logs import LogStreamEnd
from src.apps.network.nodes.observations.domain.results.logs import LogStream
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ....instances.infra.grpc.v1.openvpn_instances_pb2 import (
    OpenVPNLogsRequest,
)
from ....instances.infra.grpc.v1.openvpn_instances_pb2_grpc import (
    OpenVPNOperationsServiceStub,
)
from ...domain.dtos.logs import OpenVPNLogInput
from ...domain.results.logs import OpenVPNLogBatch
from .codec import decode


class OpenVPNLogsGateway:
    def __init__(self, streams: NodeLogStreams) -> None:
        self.streams = streams

    @asynccontextmanager
    async def follow(
        self, node: NodeModel, instance_id: str, selection: OpenVPNLogInput
    ) -> AsyncIterator[LogStream[OpenVPNLogBatch]]:
        """Borrow one native log subscription for the Panel request.

        Args:
            node: Materialized Node registry record.
            instance_id: Native OpenVPN instance identity.
            selection: Optional execution identity and resume cursor.

        Yields:
            The bounded native feed or its typed admission outcome.
        """
        request = OpenVPNLogsRequest(
            id=instance_id,
            execution_id=selection.execution_id or "",
            after_sequence=selection.after_sequence,
        )
        async with self.streams.follow(
            node.endpoint(),
            lambda channel, deadline: OpenVPNOperationsServiceStub(
                channel
            ).GetLogs(request, timeout=deadline),
            partial(decode, expected_execution=selection.execution_id),
            await_headers=False,
            failed_precondition=LogStreamEnd.PRECONDITION_FAILED,
        ) as feed:
            yield feed
