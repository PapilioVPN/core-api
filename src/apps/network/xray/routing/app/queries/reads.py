"""Read the routing state of an enabled registered Xray instance."""

from src.apps.network.nodes.app.interfaces.services import INodeService
from src.apps.network.nodes.domain.enums.observation import NodeReadStatus
from src.apps.network.nodes.domain.results.observation import NodeObservation

from ...domain.dtos.probe import XrayRouteProbe
from ...domain.results.reads import (
    XrayBalancerInfo,
    XrayRouteSelection,
    XrayRoutingRule,
)
from ..interfaces.reads import IXrayRoutingReader


class XrayRoutingQuery:
    def __init__(
        self, nodes: INodeService, gateway: IXrayRoutingReader
    ) -> None:
        self.nodes = nodes
        self.gateway = gateway

    async def list_rules(
        self, node_id: int, instance_id: str
    ) -> NodeObservation[tuple[XrayRoutingRule, ...]]:
        """Observe ordered routing rules for an enabled Node.

        Args:
            node_id: Stable node registry identity.
            instance_id: Native Xray runtime identity.

        Returns:
            The live observation or a typed availability outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.list_rules(node, instance_id)
        else:
            result = NodeObservation[tuple[XrayRoutingRule, ...]](
                NodeReadStatus.DISABLED
            )
        return result

    async def get_balancer(
        self, node_id: int, instance_id: str, tag: str
    ) -> NodeObservation[XrayBalancerInfo]:
        """Observe one balancer for an enabled Node.

        Args:
            node_id: Stable node registry identity.
            instance_id: Native Xray runtime identity.
            tag: Exact native balancer tag.

        Returns:
            The live observation or a typed availability outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.get_balancer(node, instance_id, tag)
        else:
            result = NodeObservation[XrayBalancerInfo](NodeReadStatus.DISABLED)
        return result

    async def simulate(
        self, node_id: int, instance_id: str, data: XrayRouteProbe
    ) -> NodeObservation[XrayRouteSelection]:
        """Observe one route selection for an enabled Node.

        Args:
            node_id: Stable node registry identity.
            instance_id: Native Xray runtime identity.
            data: The validated probe evaluated by the selected execution.

        Returns:
            The live observation or a typed availability outcome.

        Raises:
            NotFoundException: The Node is absent from the registry.
        """
        node = await self.nodes.get_by_id(node_id)
        if node.is_enabled:
            result = await self.gateway.simulate(node, instance_id, data)
        else:
            result = NodeObservation[XrayRouteSelection](
                NodeReadStatus.DISABLED
            )
        return result
