"""PostgreSQL storage for customer payments."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from ...domain.models.records import PaymentModel


class PaymentTable(PaymentModel, BaseTable, table=True):
    __table_args__ = (
        Index("ix_payments_customer", "customer_id", "id"),
        Index("ix_payments_card", "card_id", "id"),
        Index("ix_payments_status", "status", "id"),
    )
