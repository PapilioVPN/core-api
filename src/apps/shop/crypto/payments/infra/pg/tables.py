"""Discover the cryptocurrency payment table through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import CryptoPaymentModel


class CryptoPaymentTable(CryptoPaymentModel, BaseTable, table=True):
    pass
