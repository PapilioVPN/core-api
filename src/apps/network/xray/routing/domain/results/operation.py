"""Materialized control data carried outside the database scope."""

from dataclasses import dataclass, field
from datetime import datetime

from ..enums.operation import RoutingAction, RoutingFailure, RoutingState


@dataclass(frozen=True, slots=True)
class RoutingPayload:
    digest: str
    ciphertext: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class RoutingTarget:
    node_id: int
    instance_id: str
    address: str
    port: int
    action: RoutingAction
    deadline_at: datetime
    payload: RoutingPayload = field(repr=False)


@dataclass(frozen=True, slots=True)
class RoutingOutcome:
    state: RoutingState
    reason: RoutingFailure | None = None
