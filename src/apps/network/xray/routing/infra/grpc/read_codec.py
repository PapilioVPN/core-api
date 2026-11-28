"""Preserve native ordering and presence in Xray routing observations."""

from ...domain.results.reads import (
    XrayBalancerInfo,
    XrayRouteSelection,
    XrayRoutingRule,
)
from .v1 import routing_pb2 as wire


def decode_rules(reply: wire.XrayRoutingRules) -> tuple[XrayRoutingRule, ...]:
    """Preserve the native rule order and repeated or empty tags."""
    return tuple(
        XrayRoutingRule(row.rule_tag, row.outbound_tag) for row in reply.rules
    )


def decode_balancer(reply: wire.XrayBalancerInfo) -> XrayBalancerInfo:
    """Distinguish omitted values from an empty override or list."""
    return XrayBalancerInfo(
        reply.override_target if reply.HasField("override_target") else None,
        tuple(reply.reported_targets.tags)
        if reply.HasField("reported_targets")
        else None,
    )


def decode_route(reply: wire.XrayRouteSelection) -> XrayRouteSelection:
    """Decode the selected outbound and the native group order."""
    return XrayRouteSelection(
        reply.outbound_tag, tuple(reply.outbound_group_tags)
    )
