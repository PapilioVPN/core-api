"""Persist the intent and evidence of one configured Xray start."""

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
from sqlalchemy import text
from sqlmodel import Field

from ..enums.start import XrayExecutionAction, XrayStartReason, XrayStartState


class XrayStartModel(PersistenceEntity):
    node_id: int = ForeignKeyField("tbl_nodes.id", ondelete="RESTRICT")
    instance_id: str = CharField(63)
    request_key: UUID = Field(nullable=False)
    address: str = CharField(253)
    port: int = IntField()
    action: XrayExecutionAction = EnumField(
        XrayExecutionAction,
        length=12,
        default=XrayExecutionAction.START,
        server_default=text("'start'"),
    )
    revision_id: int | None = ForeignKeyField(
        "tbl_xray_revisions.id",
        ondelete="RESTRICT",
        nullable=True,
        default=None,
    )
    state: XrayStartState = EnumField(
        XrayStartState, length=12, default=XrayStartState.QUEUED
    )
    started_at: datetime | None = TimestampField(nullable=True, default=None)
    deadline_at: datetime | None = TimestampField(nullable=True, default=None)
    finished_at: datetime | None = TimestampField(nullable=True, default=None)
    stopped_at: datetime | None = TimestampField(nullable=True, default=None)
    reason: XrayStartReason | None = EnumField(
        XrayStartReason, length=24, nullable=True, default=None
    )
    applied_config_sha256: str | None = CharField(
        64, nullable=True, default=None
    )

    def observed_at(self, now: datetime) -> Self:
        """Project an elapsed dispatch with no persisted result."""
        record = self
        if (
            self.state is XrayStartState.RUNNING
            and self.deadline_at is not None
            and self.deadline_at <= now
        ):
            record = self.model_copy(
                update={
                    "state": XrayStartState.UNKNOWN,
                    "reason": XrayStartReason.DISPATCH_EXPIRED,
                    "finished_at": self.deadline_at,
                }
            )
        return record
