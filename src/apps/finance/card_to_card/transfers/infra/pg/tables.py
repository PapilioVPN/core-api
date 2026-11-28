"""Discover the incoming card transfer table through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import TransferModel


class CardTransferTable(TransferModel, BaseTable, table=True):
    pass
