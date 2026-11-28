"""Read the count through the pinned AccountsService over Node's channel."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel
from src.apps.network.xray.instances.infra.grpc.v1.accounts_pb2 import (
    CountVLESSAccountsRequest,
)
from src.apps.network.xray.instances.infra.grpc.v1.accounts_pb2_grpc import (
    XrayAccountsServiceStub,
)


class XrayVlessCountGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def get(
        self, node: NodeModel, instance_id: str, inbound_tag: str
    ) -> NodeObservation[int]:
        """Forward one bounded RPC and preserve a legitimate zero count."""
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayAccountsServiceStub(
                channel
            ).CountVLESSAccounts(
                CountVLESSAccountsRequest(
                    id=instance_id, inbound_tag=inbound_tag
                ),
                timeout=3,
            ),
            lambda reply: reply.count if reply.count >= 0 else None,
        )
        return result
