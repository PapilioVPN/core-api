"""Discover the crypto exchange rate table through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import CryptoRateModel


class CryptoRateTable(CryptoRateModel, BaseTable, table=True):
    pass
