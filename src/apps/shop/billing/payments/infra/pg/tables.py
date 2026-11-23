"""PostgreSQL storage for the current payment records."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from ...domain.models.records import PaymentModel


class PaymentTable(PaymentModel, BaseTable, table=True):
    __table_args__ = (
        Index("ix_tbl_payments_customer", "customer_id", "id"),
        Index("ix_tbl_payments_source", "source_id", "source", "id"),
        Index("ix_tbl_payments_status", "status", "id"),
    )
