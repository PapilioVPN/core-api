"""The original payment amount in rials and the selected gateway."""

from papilio.infra.db.schema.entity import IdentifiedEntity
from papilio.infra.db.schema.fields import BigIntField, ForeignKeyField


class CryptoPaymentModel(IdentifiedEntity):
    gateway_id: int = ForeignKeyField(
        "tbl_crypto_gateways.id", ondelete="RESTRICT", index=True
    )
    amount: int = BigIntField()
