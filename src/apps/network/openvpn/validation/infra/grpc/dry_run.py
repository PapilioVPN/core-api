"""Call the versioned OpenVPN ValidateConfig RPC."""

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation
from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.infra.grpc.observation import observe

from ....instances.infra.grpc.v1 import openvpn_instances_pb2 as wire
from ....instances.infra.grpc.v1.openvpn_instances_pb2_grpc import (
    OpenVPNConfigsServiceStub,
)
from ...domain.results.dry_run import OpenVPNValidation
from .codec import decode


class OpenVPNValidationGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def validate(
        self, node: NodeModel, instance_id: str, source: bytes
    ) -> NodeObservation[OpenVPNValidation]:
        """Call once using the registered TLS target and a bounded deadline.

        Args:
            node: Registered endpoint selected by the owning operation.
            instance_id: Native OpenVPN target identity.
            source: Exact candidate bytes supplied by the Panel.

        Returns:
            A typed reply or an availability status without raw diagnostics.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: OpenVPNConfigsServiceStub(channel).ValidateConfig(
                wire.ValidateOpenVPNConfigRequest(
                    id=instance_id, config_text=source
                ),
                timeout=5,
            ),
            lambda reply: decode(reply, instance_id),
        )
        return result
