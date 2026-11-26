"""Discover customer wallet balances through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import WalletBalanceModel


class WalletBalanceTable(WalletBalanceModel, BaseTable, table=True):
    pass
