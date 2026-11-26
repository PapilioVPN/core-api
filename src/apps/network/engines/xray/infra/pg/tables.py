"""Register Xray revisions and start operations in PostgreSQL metadata."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.revisions import XrayRevisionModel
from ...domain.models.start import XrayStartModel


class XrayRevisionTable(XrayRevisionModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint("config_sha256", name="uq_xray_revisions_digest"),
    )


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
