"""Materialized probe identities and per-run summary."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NodeProbeTarget:
    id: int
    address: str
    port: int


@dataclass(frozen=True, slots=True)
class NodeProbeClaim:
    target: NodeProbeTarget
    started_at: datetime


@dataclass(frozen=True, slots=True)
class NodeProbeBatch:
    selected: int
    recorded: int
