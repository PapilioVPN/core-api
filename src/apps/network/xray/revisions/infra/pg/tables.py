"""Register immutable Xray revisions in PostgreSQL metadata."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.records import XrayRevisionModel


class XrayRevisionTable(XrayRevisionModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint("config_sha256", name="uq_xray_revisions_digest"),
        Index(
            "ix_xray_revisions_display_order",
            text("coalesce(sort_order, -id)"),
            "id",
        ),
    )
