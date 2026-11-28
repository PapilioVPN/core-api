"""Use the selected enabled registry entry for OpenVPN dry run."""

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.domain.enums.observation import NodeReadStatus
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.dtos.dry_run import OpenVPNCandidate
from ...domain.results.dry_run import OpenVPNValidation
from ..interfaces.dry_run import IOpenVPNValidationGateway


class OpenVPNValidationService:
    def __init__(
        self, nodes: INodeService, gateway: IOpenVPNValidationGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def validate(
        self, node_id: int, instance_id: str, data: OpenVPNCandidate
    ) -> NodeObservation[OpenVPNValidation]:
        """Check a proposed configuration on one registered Node.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native OpenVPN target identity.
            data: Proposed configuration bytes under the native source field.

        Returns:
            The typed observation or its availability status.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.validate(
                node, instance_id, data.config_text
            )
        else:
            result = NodeObservation[OpenVPNValidation](
                NodeReadStatus.DISABLED
            )
        return result
