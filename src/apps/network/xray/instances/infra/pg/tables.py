"""Register Xray start operations in PostgreSQL metadata."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.rollout import (
    XrayRestartRolloutModel,
    XrayRestartRolloutTargetModel,
)
from ...domain.models.start import XrayStartModel


class XrayStartTable(XrayStartModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint(
            "node_id",
            "instance_id",
            "request_key",
            name="uq_xray_start_request",
        ),
        Index(
            "uq_xray_start_active",
            "node_id",
            "instance_id",
            unique=True,
            postgresql_where=text("state IN ('queued', 'running')"),
        ),
    )


class XrayRestartRolloutTable(XrayRestartRolloutModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint(
            "request_key", name="uq_xray_restart_rollout_request"
        ),
    )


class XrayRestartRolloutTargetTable(
    XrayRestartRolloutTargetModel, BaseTable, table=True
):
    __table_args__ = (
        UniqueConstraint(
            "rollout_id", "position", name="uq_xray_restart_rollout_position"
        ),
        UniqueConstraint(
            "rollout_id",
            "node_id",
            "instance_id",
            name="uq_xray_restart_rollout_target",
        ),
        UniqueConstraint(
            "operation_id", name="uq_xray_restart_rollout_operation"
        ),
    )
