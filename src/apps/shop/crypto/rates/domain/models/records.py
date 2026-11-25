"""Shared rates in rials per unit of a pricing currency."""

from decimal import Decimal

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import CharField, NumericField


class CryptoRateModel(IdentifiedEntity):
    currency: str = CharField(3, unique=True)
    rial_rate: Decimal = NumericField()
