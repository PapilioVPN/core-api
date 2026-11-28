"""Call the versioned Hysteria ValidateConfig RPC."""

from src.apps.network.nodes.connections.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.connections.infra.grpc.observation import observe
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.domain.models.records import NodeModel

from ...domain.results.dry_run import HysteriaValidation
from .codec import decode
from .v1.hysteria_configs_pb2 import ValidateHysteriaConfigRequest
from .v1.hysteria_configs_pb2_grpc import HysteriaConfigsServiceStub


class HysteriaValidationGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def validate(
        self, node: NodeModel, instance_id: str, source: bytes
    ) -> NodeObservation[HysteriaValidation]:
        """Call once using the registered TLS target and a bounded deadline.

        Args:
            node: Registered endpoint selected by the owning operation.
            instance_id: Native Hysteria target identity.
            source: Exact candidate bytes supplied by the Panel.

        Returns:
            A typed reply or an availability status without raw diagnostics.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: HysteriaConfigsServiceStub(channel).ValidateConfig(
                ValidateHysteriaConfigRequest(
                    id=instance_id, config_yaml=source
                ),
                timeout=5,
            ),
            lambda reply: decode(reply, instance_id),
        )
        return result
