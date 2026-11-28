"""Ordered rules, balancer presence and a simulated Xray selection."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class XrayRoutingRule:
    rule_tag: str
    outbound_tag: str


@dataclass(frozen=True, slots=True)
class XrayBalancerInfo:
    override_target: str | None
    reported_targets: tuple[str, ...] | None


@dataclass(frozen=True, slots=True)
class XrayRouteSelection:
    outbound_tag: str
    outbound_group_tags: tuple[str, ...]
