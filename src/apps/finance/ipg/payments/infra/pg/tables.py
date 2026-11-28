"""Discover IPG payments through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.records import PaymentModel


class IPGPaymentTable(PaymentModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint("gateway_id", "reference"),
        Index(
            "ix_ipg_payments_due",
            "next_check_at",
            "id",
            postgresql_where=text(
                "status = 'ready' AND next_check_at IS NOT NULL"
            ),
        ),
    )
