"""Register Xray revisions in PostgreSQL metadata."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import UniqueConstraint

from ...domain.models.revisions import XrayRevisionModel


class XrayRevisionTable(XrayRevisionModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint("config_sha256", name="uq_xray_revisions_digest"),
    )
