"""Call the versioned OpenVPN GetStatus RPC."""

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation
from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.infra.grpc.observation import observe

from ...domain.results.status import OpenVPNStatus
from .codec import decode
from .v1.openvpn_instances_pb2 import OpenVPNInstanceRequest
from .v1.openvpn_instances_pb2_grpc import OpenVPNInstancesServiceStub


class OpenVPNStatusGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def read(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[OpenVPNStatus]:
        """Call once using the registered TLS target and a bounded deadline.

        Args:
            node: Registered endpoint selected by the owning operation.
            instance_id: Native OpenVPN target identity.

        Returns:
            A typed reply or an availability status without raw diagnostics.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: OpenVPNInstancesServiceStub(channel).GetStatus(
                OpenVPNInstanceRequest(id=instance_id), timeout=3
            ),
            lambda reply: decode(reply, instance_id),
        )
        return result
