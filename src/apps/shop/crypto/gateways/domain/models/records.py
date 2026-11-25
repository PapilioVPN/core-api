"""A crypto gateway account and its editable sales settings."""

from decimal import Decimal

from papilio.infra.db.dialects.postgresql import JSONBField
from papilio.infra.db.schema.entity import PersistenceEntity, TimestampEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    ForeignKeyField,
    NumericField,
)
from pydantic import JsonValue


class CryptoGatewayModel(PersistenceEntity):
    key: str = CharField(55, unique=True)
    title: str = CharField(55)
    icon_url: str | None = CharField(255, nullable=True, default=None)
    # Imported payment history may have an account key without configuration.
    kind: str | None = CharField(55, nullable=True, default=None)
    price_currency: str | None = CharField(64, nullable=True, default=None)
    pay_currency: str | None = CharField(64, nullable=True, default=None)
    rial_rate: Decimal | None = NumericField(
        24, 8, nullable=True, default=None
    )
    is_active: bool = BoolField(default=False)


class CryptoGatewayConfigModel(TimestampEntity):
    gateway_id: int = ForeignKeyField(
        "tbl_crypto_gateways.id", primary_key=True, ondelete="CASCADE"
    )
    config: dict[str, JsonValue] = JSONBField()
