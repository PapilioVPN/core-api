"""Discover the cryptocurrency payment table through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, text

from ...domain.models.records import CryptoPaymentModel


class CryptoPaymentTable(CryptoPaymentModel, BaseTable, table=True):
    __table_args__ = (
        Index(
            "ix_crypto_payments_due",
            text("last_check_at NULLS FIRST"),
            "id",
            postgresql_where=text(
                "confirmed_at IS NULL AND invoice_id IS NOT NULL"
            ),
        ),
    )
