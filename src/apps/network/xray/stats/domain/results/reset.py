"""Evidence from one dispatched reset and its materialized target."""

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from ..enums.reset import (
    ResetEffect,
    ResetKind,
    ResetReason,
    ResetState,
    TrafficDirection,
)
from ..enums.traffic import XrayTrafficScope


class ResetCounterEvidence(TypedDict):
    name: str
    direction: TrafficDirection
    effect: ResetEffect
    previous_bytes: int | None


@dataclass(frozen=True, slots=True)
class ResetSelection:
    scope: XrayTrafficScope
    kind: ResetKind
    name: str | None = None
    direction: TrafficDirection | None = None
    max_counters: int | None = None


@dataclass(frozen=True, slots=True)
class ResetTarget:
    node_id: int
    instance_id: str
    address: str
    port: int
    selection: ResetSelection
    deadline_at: datetime


@dataclass(frozen=True, slots=True)
class ResetOutcome:
    state: ResetState
    reason: ResetReason | None = None
    counters: tuple[ResetCounterEvidence, ...] = ()
