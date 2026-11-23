"""PostgreSQL persistence for customer receipts."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import ReceiptModel


class ReceiptTable(ReceiptModel, BaseTable, table=True):
    pass
