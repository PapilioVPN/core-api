"""Discover wallet top-up requests through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import Index

from ...domain.models.records import WalletDepositModel


class WalletDepositTable(WalletDepositModel, BaseTable, table=True):
    __table_args__ = (
        Index("ix_wallet_deposits_customer", "customer_id", "id"),
    )
