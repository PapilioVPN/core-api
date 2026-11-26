"""Stored cryptocurrency gateway accounts."""

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import BigIntField, BoolField, CharField
from sqlalchemy import false


class CryptoGatewayModel(IdentifiedEntity):
    kind: str = CharField(55)
    title: str = CharField(55)
    icon_url: str | None = CharField(255, nullable=True, default=None)
    is_active: bool = BoolField(default=False, server_default=false())
    min_amount: int | None = BigIntField(nullable=True, default=None)
    max_amount: int | None = BigIntField(nullable=True, default=None)
