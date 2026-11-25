"""A crypto gateway account and its editable sales settings."""

from decimal import Decimal

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import BoolField, CharField, NumericField


class CryptoGatewayModel(PersistenceEntity):
    key: str = CharField(55, unique=True)
    title: str = CharField(55)
    # Imported payment history may have an account key without configuration.
    kind: str | None = CharField(55, nullable=True, default=None)
    price_currency: str | None = CharField(64, nullable=True, default=None)
    pay_currency: str | None = CharField(64, nullable=True, default=None)
    rial_rate: Decimal | None = NumericField(
        24, 8, nullable=True, default=None
    )
    is_active: bool = BoolField(default=False)
