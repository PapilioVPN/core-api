"""Call the versioned WireGuard ValidateConfig RPC."""

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation
from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.infra.grpc.observation import observe

from ...domain.results.dry_run import WireGuardValidation
from .v1.interfaces_pb2 import WireGuardValidateConfigRequest
from .v1.interfaces_pb2_grpc import WireGuardInterfacesServiceStub
from .validation import decode


class WireGuardValidationGateway:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def validate(
        self, node: NodeModel, target_name: str, source: bytes
    ) -> NodeObservation[WireGuardValidation]:
        """Call once using the registered TLS target and a bounded deadline.

        Args:
            node: Registered endpoint selected by the owning operation.
            target_name: Native WireGuard target identity.
            source: Exact candidate bytes supplied by the Panel.

        Returns:
            A typed reply or an availability status without raw diagnostics.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: WireGuardInterfacesServiceStub(
                channel
            ).ValidateConfig(
                WireGuardValidateConfigRequest(
                    name=target_name, config_json=source
                ),
                timeout=5,
            ),
            decode,
        )
        return result
