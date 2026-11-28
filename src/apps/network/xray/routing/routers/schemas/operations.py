"""Expose routing delivery evidence without the submitted source."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.operation import (
    RoutingAction,
    RoutingFailure,
    RoutingState,
)


class RoutingOperationOutput(BaseOutput):
    id: int
    node_id: int
    instance_id: str
    action: RoutingAction
    state: RoutingState
    reason: RoutingFailure | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
