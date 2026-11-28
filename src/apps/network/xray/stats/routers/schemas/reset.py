"""Panel tracking for technical traffic resets and per-counter evidence."""

from datetime import datetime
from typing import Self

from papilio.schemas.outputs import BaseOutput

from ...domain.enums.reset import (
    ResetEffect,
    ResetKind,
    ResetReason,
    ResetState,
    TrafficDirection,
)
from ...domain.enums.traffic import XrayTrafficScope
from ...domain.models.reset import XrayTrafficResetModel


class ResetCounterOutput(BaseOutput):
    name: str
    direction: TrafficDirection
    effect: ResetEffect
    previous_bytes: str | None


class TrafficResetOutput(BaseOutput):
    id: int
    node_id: int
    instance_id: str
    scope: XrayTrafficScope
    kind: ResetKind
    name: str | None
    direction: TrafficDirection | None
    max_counters: int | None
    state: ResetState
    reason: ResetReason | None
    counters: list[ResetCounterOutput] | None
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_reset(cls, record: XrayTrafficResetModel) -> Self:
        """Keep signed 64-bit byte totals exact for browser clients."""
        counters = None
        if record.counters is not None:
            counters = []
            for row in record.counters:
                previous = row["previous_bytes"]
                counters.append(
                    ResetCounterOutput(
                        name=row["name"],
                        direction=row["direction"],
                        effect=row["effect"],
                        previous_bytes=str(previous)
                        if previous is not None
                        else None,
                    )
                )
        return cls(
            id=record.id,
            node_id=record.node_id,
            instance_id=record.instance_id,
            scope=record.scope,
            kind=record.kind,
            name=record.name,
            direction=record.direction,
            max_counters=record.max_counters,
            state=record.state,
            reason=record.reason,
            counters=counters,
            created_at=record.created_at,
            started_at=record.started_at,
            finished_at=record.finished_at,
        )
