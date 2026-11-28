"""Discover online payment gateway accounts through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import ForeignKeyConstraint

from ...domain.models.configs import ConfigModel
from ...domain.models.records import GatewayModel


class IPGGatewayTable(GatewayModel, BaseTable, table=True):
    pass


class IPGConfigTable(ConfigModel, BaseTable, table=True):
    __table_args__ = (
        ForeignKeyConstraint(["key"], ["tbl_ipg_gateways.kind"]),
    )
