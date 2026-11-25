"""Discover crypto payment records through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import UniqueConstraint

from ...domain.models.records import CryptoPaymentModel


class CryptoPaymentTable(CryptoPaymentModel, BaseTable, table=True):
    __table_args__ = (
        UniqueConstraint(
            "gateway_id", "invoice_id", name="uq_crypto_payment_invoice"
        ),
    )
