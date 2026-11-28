"""Panel output for the managed node registry."""

from datetime import datetime
from typing import Self

from papilio.schemas.outputs import BaseOutput
from pydantic import BaseModel

from src.apps.network.nodes.connections.domain.enums.connection import (
    NodeConnectionStatus,
)

from ...domain.enums.state import NodeStateStatus
from ...domain.models.records import NodeModel


class NodeOutput(BaseOutput):
    id: int
    name: str
    address: str
    port: int
    default_timeout: int
    is_enabled: bool
    connection_status: NodeConnectionStatus
    last_checked_at: datetime | None
    last_seen_at: datetime | None
    connection_stale: bool = False
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, node: NodeModel, *, stale_before: datetime) -> Self:
        """Expose freshness separately from the last recorded outcome."""
        output = cls.from_obj(node)
        output.connection_stale = (
            node.last_checked_at is not None
            and node.last_checked_at <= stale_before
        )
        return output


class NodeChoiceOutput(BaseOutput):
    id: int
    name: str
    is_enabled: bool


class NodeSelectionMeta(BaseModel):
    next_before_id: int | None


class NodeStateOutput(BaseOutput):
    node_id: int
    status: NodeStateStatus
    is_enabled: bool | None
