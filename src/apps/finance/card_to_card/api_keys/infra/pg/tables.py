"""Discover the card transfer API keys table through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import APIKeyModel


class CardAPIKeyTable(APIKeyModel, BaseTable, table=True):
    pass
