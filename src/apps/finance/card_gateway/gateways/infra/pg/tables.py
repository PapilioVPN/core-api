"""Discover hosted card gateway accounts through Papilio."""

from papilio.infra.db.table import BaseTable
from sqlalchemy import ForeignKeyConstraint

from ...domain.models.configs import ConfigModel
from ...domain.models.records import GatewayModel


class CardGatewayTable(GatewayModel, BaseTable, table=True):
    pass


class CardGatewayConfigTable(ConfigModel, BaseTable, table=True):
    __table_args__ = (
        ForeignKeyConstraint(["key"], ["tbl_card_gateways.kind"]),
    )
