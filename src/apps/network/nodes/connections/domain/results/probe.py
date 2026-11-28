"""Materialized probe identities and per-run summary."""

from dataclasses import dataclass
from datetime import datetime

from src.apps.network.nodes.registry.domain.results.records import NodeEndpoint


@dataclass(frozen=True, slots=True)
class NodeProbeClaim:
    target: NodeEndpoint
    started_at: datetime


@dataclass(frozen=True, slots=True)
class NodeProbeBatch:
    selected: int
    recorded: int
