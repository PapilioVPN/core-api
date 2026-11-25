"""The original rial payment, selected gateway and optional frozen quote."""

from decimal import Decimal

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    ForeignKeyField,
    NumericField,
    TextField,
)


class CryptoPaymentModel(IdentifiedEntity):
    gateway_id: int = ForeignKeyField(
        "tbl_crypto_gateways.id", ondelete="RESTRICT", index=True
    )
    amount: int = BigIntField()
    quote_amount: Decimal | None = NumericField(nullable=True, default=None)
    quote_currency: str | None = CharField(3, nullable=True, default=None)
    quote_rate: Decimal | None = NumericField(nullable=True, default=None)
    invoice_id: str | None = CharField(64, nullable=True, default=None)
    invoice_url: str | None = TextField(nullable=True, default=None)
