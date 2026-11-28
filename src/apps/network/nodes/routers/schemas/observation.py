"""Common Node target and delivery information for engine observations."""

from datetime import datetime

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.observation import NodeReadStatus


class NodeObservationOutput(BaseOutput):
    node_id: int
    status: NodeReadStatus
    received_at: datetime | None
