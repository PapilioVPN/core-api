"""Discover PostgreSQL crypto gateway records."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import CryptoGatewayModel


class CryptoGatewayTable(CryptoGatewayModel, BaseTable, table=True):
    pass
