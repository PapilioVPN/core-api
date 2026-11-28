"""Use the selected enabled registry entry for WireGuard dry run."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.dtos.dry_run import WireGuardCandidate
from ...domain.results.dry_run import WireGuardValidation
from ..interfaces.dry_run import IWireGuardValidationGateway


class WireGuardValidationService:
    def __init__(
        self, nodes: INodeService, gateway: IWireGuardValidationGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def validate(
        self, node_id: int, target_name: str, data: WireGuardCandidate
    ) -> NodeObservation[WireGuardValidation]:
        """Check a proposed configuration on one registered Node.

        Args:
            node_id: Stable Node registry identity.
            target_name: Native WireGuard target identity.
            data: Proposed configuration bytes under the native source field.

        Returns:
            The typed observation or its availability status.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.validate(
                node, target_name, data.config_json
            )
        else:
            result = NodeObservation[WireGuardValidation](
                NodeReadStatus.DISABLED
            )
        return result
