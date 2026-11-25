"""Shared rates in rials per unit of a pricing currency."""

from datetime import datetime
from decimal import Decimal

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    CharField,
    NumericField,
    TimestampField,
)


class CryptoRateModel(IdentifiedEntity):
    currency: str = CharField(3, unique=True)
    rial_rate: Decimal = NumericField()
    source: str | None = CharField(24, nullable=True, default=None)
    fetched_at: datetime | None = TimestampField(nullable=True, default=None)
