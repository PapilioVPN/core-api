"""Register the durable Xray reset table."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.reset import XrayTrafficResetModel


class XrayTrafficResetTable(XrayTrafficResetModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint(
            "node_id",
            "instance_id",
            "request_key",
            name="uq_xray_reset_request",
        ),
        Index(
            "uq_xray_reset_active",
            "node_id",
            "instance_id",
            unique=True,
            postgresql_where=text("state IN ('queued', 'running')"),
        ),
    )
