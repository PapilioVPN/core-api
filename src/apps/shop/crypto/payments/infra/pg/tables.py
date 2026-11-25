"""Discover crypto payment records through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index, UniqueConstraint, text

from ...domain.models.records import CryptoPaymentModel


class CryptoPaymentTable(CryptoPaymentModel, BaseTable, table=True):
    __table_args__ = (
        Index(
            "ix_crypto_payments_recheck",
            text("coalesce(checked_at, created_at)"),
            "id",
            postgresql_where=text(
                "invoice_id IS NOT NULL AND status IN ('pending', 'partial')"
            ),
        ),
        UniqueConstraint(
            "gateway_id", "invoice_id", name="uq_crypto_payment_invoice"
        ),
        UniqueConstraint(
            "gateway_id",
            "provider_payment_id",
            name="uq_crypto_provider_payment",
        ),
    )
