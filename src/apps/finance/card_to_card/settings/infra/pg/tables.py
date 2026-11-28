"""Discover the card transfer settings table through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import TransferSettingsModel


class CardTransferSettingsTable(TransferSettingsModel, BaseTable, table=True):
    table_name = "tbl_card_transfer_settings"
