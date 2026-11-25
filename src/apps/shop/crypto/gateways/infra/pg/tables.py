"""Discover the gateway account table through Papilio."""

from papilio.infra.db.table import BaseTable

from ...domain.models.configs import GatewayConfigModel
from ...domain.models.records import CryptoGatewayModel


class CryptoGatewayTable(CryptoGatewayModel, BaseTable, table=True):
    pass


class CryptoGatewayConfigTable(GatewayConfigModel, BaseTable, table=True):
    pass
