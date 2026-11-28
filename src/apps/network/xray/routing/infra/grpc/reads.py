"""Issue one bounded direct call for each native routing observation."""

from src.apps.network.nodes.domain.models.records import NodeModel
from src.apps.network.nodes.domain.results.observation import NodeObservation
from src.apps.network.nodes.infra.grpc.channels import NodeChannels
from src.apps.network.nodes.infra.grpc.observation import observe

from ...domain.dtos.probe import XrayRouteProbe
from ...domain.results.reads import (
    XrayBalancerInfo,
    XrayRouteSelection,
    XrayRoutingRule,
)
from .read_codec import decode_balancer, decode_route, decode_rules
from .v1 import routing_pb2 as wire
from .v1.routing_pb2_grpc import XrayRoutingServiceStub


class XrayRoutingReader:
    def __init__(self, channels: NodeChannels) -> None:
        self.channels = channels

    async def list_rules(
        self, node: NodeModel, instance_id: str
    ) -> NodeObservation[tuple[XrayRoutingRule, ...]]:
        """Observe ordered routing rules on Node's authenticated channel.

        Args:
            node: Materialized node registry record.
            instance_id: Native Xray runtime identity.

        Returns:
            A bounded snapshot or a typed read outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayRoutingServiceStub(channel).ListRoutingRules(
                wire.XrayRoutingRulesRequest(id=instance_id), timeout=2
            ),
            decode_rules,
        )
        return result

    async def get_balancer(
        self, node: NodeModel, instance_id: str, tag: str
    ) -> NodeObservation[XrayBalancerInfo]:
        """Observe one balancer on Node's authenticated channel.

        Args:
            node: Materialized node registry record.
            instance_id: Native Xray runtime identity.
            tag: Exact native balancer tag.

        Returns:
            A bounded snapshot or a typed read outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayRoutingServiceStub(channel).GetBalancerInfo(
                wire.XrayBalancerInfoRequest(id=instance_id, tag=tag),
                timeout=2,
            ),
            decode_balancer,
        )
        return result

    async def simulate(
        self, node: NodeModel, instance_id: str, data: XrayRouteProbe
    ) -> NodeObservation[XrayRouteSelection]:
        """Observe one route selection on Node's authenticated channel.

        Args:
            node: Materialized node registry record.
            instance_id: Native Xray runtime identity.
            data: The validated probe evaluated by the selected execution.

        Returns:
            A bounded snapshot or a typed read outcome.
        """
        result = await observe(
            self.channels,
            node,
            lambda channel: XrayRoutingServiceStub(channel).TestRoute(
                wire.XrayTestRouteRequest(
                    id=instance_id,
                    inbound_tag=data.inbound_tag,
                    network=data.network,
                    target_ip=str(data.target_ip)
                    if data.target_ip is not None
                    else "",
                    target_domain=data.target_domain,
                    target_port=data.target_port,
                    protocol=data.protocol,
                    user=data.user,
                    attributes=data.attributes,
                ),
                timeout=2,
            ),
            decode_route,
        )
        return result
