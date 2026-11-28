"""Use the selected enabled registry entry for Hysteria dry run."""

from src.apps.network.nodes.observations.domain.enums.observation import (
    NodeReadStatus,
)
from src.apps.network.nodes.observations.domain.results.observation import (
    NodeObservation,
)
from src.apps.network.nodes.registry.app.interfaces.services import (
    INodeService,
)

from ...domain.dtos.dry_run import HysteriaCandidate
from ...domain.results.dry_run import HysteriaValidation
from ..interfaces.dry_run import IHysteriaValidationGateway


class HysteriaValidationService:
    def __init__(
        self, nodes: INodeService, gateway: IHysteriaValidationGateway
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def validate(
        self, node_id: int, instance_id: str, data: HysteriaCandidate
    ) -> NodeObservation[HysteriaValidation]:
        """Check a proposed configuration on one registered Node.

        Args:
            node_id: Stable Node registry identity.
            instance_id: Native Hysteria target identity.
            data: Proposed configuration bytes under the native source field.

        Returns:
            The typed observation or its availability status.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.validate(
                node, instance_id, data.config_yaml
            )
        else:
            result = NodeObservation[HysteriaValidation](
                NodeReadStatus.DISABLED
            )
        return result
