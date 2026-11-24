"""PostgreSQL payment records discovered by Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import PaymentModel


class PaymentTable(PaymentModel, BaseTable, table=True):
    pass
