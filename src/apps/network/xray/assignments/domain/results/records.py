"""Materialized desired revision metadata and its live comparison."""

from dataclasses import dataclass
from datetime import datetime

from src.apps.network.nodes.domain.results.records import NodeEndpoint
from src.apps.network.xray.instances.domain.results.status import (
    XrayStatusResult,
)

from ..enums.comparison import XrayRevisionComparisonState


@dataclass(frozen=True, slots=True)
class XrayDesiredRevision:
    revision_id: int
    config_sha256: str
    updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class XrayAssignmentSelection:
    endpoint: NodeEndpoint
    desired: XrayDesiredRevision | None


@dataclass(frozen=True, slots=True)
class XrayRevisionComparison:
    state: XrayRevisionComparisonState
    desired: XrayDesiredRevision | None = None
    observed: XrayStatusResult | None = None


@dataclass(frozen=True, slots=True)
class XrayFleetComparisonItem:
    node_id: int
    instance_id: str
    comparison: XrayRevisionComparison
