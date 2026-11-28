"""Register persisted routing operations through native discovery."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.operation import XrayRoutingOperationModel


class XrayRoutingOperationTable(
    XrayRoutingOperationModel, BaseTable, table=True
):
    __table_args__ = (
        UniqueConstraint(
            "node_id",
            "instance_id",
            "request_key",
            name="uq_xray_routing_request",
        ),
        Index(
            "uq_xray_routing_active",
            "node_id",
            "instance_id",
            unique=True,
            postgresql_where=text("state IN ('queued', 'running')"),
        ),
    )
