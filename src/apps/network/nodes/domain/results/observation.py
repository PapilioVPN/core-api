"""Separate a checked or observed value from its delivery outcome."""

from dataclasses import dataclass
from datetime import datetime

from ..enums.observation import NodeReadStatus


@dataclass(frozen=True, slots=True)
class NodeObservation[T]:
    status: NodeReadStatus
    value: T | None = None
    received_at: datetime | None = None
