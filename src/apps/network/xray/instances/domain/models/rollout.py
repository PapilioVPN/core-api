"""Persist a rollout and its ordered, captured management targets."""

from datetime import datetime
from uuid import UUID

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    CharField,
    EnumField,
    ForeignKeyField,
    IntField,
    TimestampField,
)
from sqlmodel import Field

from ..enums.rollout import RestartRolloutReason, RestartRolloutState


class XrayRestartRolloutModel(PersistenceEntity):
    request_key: UUID = Field(nullable=False)
    revision_id: int = ForeignKeyField(
        "tbl_xray_revisions.id", ondelete="RESTRICT"
    )
    config_sha256: str = CharField(64)
    position: int = IntField(default=1)
    state: RestartRolloutState = EnumField(
        RestartRolloutState, length=14, default=RestartRolloutState.RUNNING
    )
    reason: RestartRolloutReason | None = EnumField(
        RestartRolloutReason,
        length=24,
        nullable=True,
        default=None,
    )
    finished_at: datetime | None = TimestampField(nullable=True, default=None)


class XrayRestartRolloutTargetModel(PersistenceEntity):
    rollout_id: int = ForeignKeyField(
        "tbl_xray_restart_rollouts.id", ondelete="RESTRICT"
    )
    position: int = IntField()
    node_id: int = ForeignKeyField("tbl_nodes.id", ondelete="RESTRICT")
    instance_id: str = CharField(63)
    address: str = CharField(253)
    port: int = IntField()
    operation_id: int | None = ForeignKeyField(
        "tbl_xray_starts.id",
        ondelete="RESTRICT",
        nullable=True,
        default=None,
    )
