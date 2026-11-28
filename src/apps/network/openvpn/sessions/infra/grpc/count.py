"""Read OpenVPNSessionCount through the pinned Node RPC."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ....instances.infra.grpc.v1.openvpn_instances_pb2 import (
    OpenVPNInstanceRequest,
    OpenVPNSessionReport,
)
from ....instances.infra.grpc.v1.openvpn_instances_pb2_grpc import (
    OpenVPNOperationsServiceStub,
)
from ...domain.results.count import OpenVPNSessionCount


def _decode(reply: OpenVPNSessionReport) -> OpenVPNSessionCount | None:
    result = None
    if bool(reply.execution_id) and reply.observed_at > 0:
        result = OpenVPNSessionCount(
            execution_id=reply.execution_id,
            observed_at_unix_seconds=reply.observed_at,
            session_count=len(reply.sessions),
        )
    return result


class OpenVPNSessionCountGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[OpenVPNSessionCount]:
        """Send one bounded request over the shared authenticated channel."""
        result = await observe(
            self.channels,
            node,
            lambda channel: OpenVPNOperationsServiceStub(channel).ListSessions(
                OpenVPNInstanceRequest(id=instance_id),
                timeout=node.default_timeout,
            ),
            _decode,
        )
        return result
