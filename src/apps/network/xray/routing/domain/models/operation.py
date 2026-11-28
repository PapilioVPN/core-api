"""Persist operator intent independently of an active Xray execution."""

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
from sqlalchemy import Text
from sqlmodel import Field

from ..enums.operation import RoutingAction, RoutingFailure, RoutingState


class XrayRoutingOperationModel(PersistenceEntity):
    node_id: int = ForeignKeyField("tbl_nodes.id", ondelete="RESTRICT")
    instance_id: str = CharField(63)
    address: str = CharField(253)
    port: int = IntField()
    request_key: UUID = Field(nullable=False)
    action: RoutingAction = EnumField(RoutingAction, length=20)
    payload_digest: str = CharField(64)
    ciphertext: str = Field(sa_type=Text, nullable=False, repr=False)
    state: RoutingState = EnumField(
        RoutingState, length=14, default=RoutingState.QUEUED
    )
    reason: RoutingFailure | None = EnumField(
        RoutingFailure, length=24, nullable=True, default=None
    )
    started_at: datetime | None = TimestampField(nullable=True, default=None)
    deadline_at: datetime | None = TimestampField(nullable=True, default=None)
    finished_at: datetime | None = TimestampField(nullable=True, default=None)

    def observed_at(self, now: datetime) -> Self:
        """Expose elapsed dispatch as uncertain even before a new write."""
        operation = self
        if (
            self.state is RoutingState.RUNNING
            and self.deadline_at is not None
            and self.deadline_at <= now
        ):
            operation = self.model_copy(
                update={
                    "state": RoutingState.UNKNOWN,
                    "reason": RoutingFailure.DISPATCH_EXPIRED,
                    "finished_at": self.deadline_at,
                }
            )
        return operation
