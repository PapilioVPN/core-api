"""PostgreSQL receipt records discovered by Papilio."""

from papilio.infra.db.schema.fields import CharField
from papilio.infra.db.table import BaseTable

from ...domain.models.records import ReceiptModel


class ReceiptTable(ReceiptModel, BaseTable, table=True):
    # Preserve data written by the published receipt review migration.
    rejection_reason: str | None = CharField(500, nullable=True, default=None)
