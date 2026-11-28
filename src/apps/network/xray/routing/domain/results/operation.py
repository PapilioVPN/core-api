"""Materialized control data carried outside the database scope."""

from dataclasses import dataclass, field
from datetime import datetime

from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint

from ..enums.operation import RoutingAction, RoutingFailure, RoutingState


@dataclass(frozen=True, slots=True)
class RoutingPayload:
    digest: str
    ciphertext: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class RoutingTarget:
    node: NodeEndpoint
    instance_id: str
    action: RoutingAction
    deadline_at: datetime
    payload: RoutingPayload = field(repr=False)


@dataclass(frozen=True, slots=True)
class RoutingOutcome:
    state: RoutingState
    reason: RoutingFailure | None = None
