"""Register one desired Xray revision per selected instance."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import UniqueConstraint

from ...domain.models.records import XrayDesiredRevisionModel


class XrayDesiredRevisionTable(
    XrayDesiredRevisionModel, BaseTable, table=True
):
    __table_args__ = (
        UniqueConstraint(
            "node_id", "instance_id", name="uq_xray_desired_revision_target"
        ),
    )
