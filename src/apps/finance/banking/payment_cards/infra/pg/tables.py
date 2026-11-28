"""PostgreSQL storage for retailer payment destination cards."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import PaymentCardModel


class PaymentCardTable(PaymentCardModel, BaseTable, table=True):
    pass
