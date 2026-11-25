"""Discover PostgreSQL crypto gateway records."""

from papilio.infra.db.table import BaseTable

from ...domain.models.records import (
    CryptoGatewayConfigModel,
    CryptoGatewayModel,
)


class CryptoGatewayTable(CryptoGatewayModel, BaseTable, table=True):
    pass


class CryptoGatewayConfigTable(
    CryptoGatewayConfigModel, BaseTable, table=True
):
    pass
