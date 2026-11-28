"""Persist the technical reset request and its final Node evidence."""

from datetime import datetime
from typing import Self
from uuid import UUID

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    CharField,
    EnumField,
    ForeignKeyField,
    IntField,
    TimestampField,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field

from ..enums.reset import ResetKind, ResetReason, ResetState, TrafficDirection
from ..enums.traffic import XrayTrafficScope
from ..results.reset import ResetCounterEvidence, ResetSelection


class XrayTrafficResetModel(PersistenceEntity):
    node_id: int = ForeignKeyField("tbl_nodes.id", ondelete="RESTRICT")
    instance_id: str = CharField(63)
    address: str = CharField(253)
    port: int = IntField()
    request_key: UUID = Field(nullable=False)
    scope: XrayTrafficScope = EnumField(XrayTrafficScope, length=12)
    kind: ResetKind = EnumField(ResetKind, length=12)
    name: str | None = CharField(4096, nullable=True, default=None)
    direction: TrafficDirection | None = EnumField(
        TrafficDirection, length=12, nullable=True, default=None
    )
    max_counters: int | None = IntField(nullable=True, default=None)
    state: ResetState = EnumField(
        ResetState, length=14, default=ResetState.QUEUED
    )
    reason: ResetReason | None = EnumField(
        ResetReason, length=24, nullable=True, default=None
    )
    counters: list[ResetCounterEvidence] | None = Field(
        sa_type=JSON, nullable=True, default=None
    )
    started_at: datetime | None = TimestampField(nullable=True, default=None)
    deadline_at: datetime | None = TimestampField(nullable=True, default=None)
    finished_at: datetime | None = TimestampField(nullable=True, default=None)

    def selection(self) -> ResetSelection:
        """Materialize the exact stored Node selection."""
        return ResetSelection(
            self.scope, self.kind, self.name, self.direction, self.max_counters
        )

    def observed_at(self, now: datetime) -> Self:
        """Project elapsed dispatch without repeating the reset."""
        operation = self
        if (
            self.state is ResetState.RUNNING
            and self.deadline_at is not None
            and self.deadline_at <= now
        ):
            operation = self.model_copy(
                update={
                    "state": ResetState.UNKNOWN,
                    "reason": ResetReason.DISPATCH_EXPIRED,
                    "finished_at": self.deadline_at,
                }
            )
        return operation
