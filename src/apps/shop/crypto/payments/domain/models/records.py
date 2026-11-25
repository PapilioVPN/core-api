"""Persist original rials, quoted terms and the issued invoice."""

from datetime import datetime
from decimal import Decimal

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    ForeignKeyField,
    NumericField,
    TextField,
    TimestampField,
)

from ..enums.records import CryptoPaymentStatus


class CryptoPaymentModel(PersistenceEntity):
    gateway_id: int = ForeignKeyField(
        "tbl_crypto_gateways.id", ondelete="RESTRICT"
    )
    amount: int = BigIntField()
    price_amount: Decimal = NumericField()
    price_currency: str = CharField(64)
    pay_currency: str | None = CharField(64, nullable=True, default=None)
    invoice_id: str | None = CharField(255, nullable=True, default=None)
    invoice_url: str | None = TextField(nullable=True, default=None)
    provider_payment_id: str | None = CharField(
        64, nullable=True, default=None
    )
    confirmed_at: datetime | None = TimestampField(nullable=True, default=None)
    status: CryptoPaymentStatus = EnumField(
        CryptoPaymentStatus, length=12, default=CryptoPaymentStatus.PENDING
    )
