"""Discover the wallet transaction journal through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import WalletTransactionModel


class WalletTransactionTable(WalletTransactionModel, BaseTable, table=True):
    pass
