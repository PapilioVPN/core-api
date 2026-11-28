"""Managed node registry table discovered by Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.records import NodeModel


class NodeTable(NodeModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint("address", "port", name="uq_nodes_endpoint"),
        Index(
            "ix_nodes_display_order", text("coalesce(sort_order, -id)"), "id"
        ),
        Index(
            "ix_nodes_probe_due",
            text("probe_started_at NULLS FIRST"),
            "id",
            postgresql_where=text("is_enabled"),
        ),
    )
