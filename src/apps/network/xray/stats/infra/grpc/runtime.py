"""Read runtime metrics over Xray's versioned Node contract."""

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation
from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.infra.grpc.observation import observe

from ...domain.results.runtime import XrayRuntime
from .codec import decode_runtime
from .v1.runtime_stats_pb2 import XrayRuntimeStatsRequest
from .v1.runtime_stats_pb2_grpc import XrayStatsServiceStub


class XrayRuntimeGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[XrayRuntime]:
        """Issue one bounded read on the selected Node channel.

        Args:
            node: Materialized registry endpoint.
            instance_id: Native instance identity.

        Returns:
            A typed snapshot or an availability outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayStatsServiceStub(channel).GetRuntimeStats(
                XrayRuntimeStatsRequest(id=instance_id), timeout=3
            ),
            decode_runtime,
        )
        return result
