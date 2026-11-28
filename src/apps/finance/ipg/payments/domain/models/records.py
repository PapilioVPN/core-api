"""Store IPG payment terms and provider link evidence."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    ForeignKeyField,
    TextField,
)

from ..enums.records import LinkStatus


class PaymentModel(PersistenceEntity):
    gateway_id: int = ForeignKeyField("tbl_ipg_gateways.id")
    amount: int = BigIntField()
    description: str = CharField(255)
    status: LinkStatus = EnumField(
        LinkStatus, length=16, default=LinkStatus.ISSUING
    )
    reference: str | None = CharField(128, default=None, nullable=True)
    pay_url: str | None = TextField(default=None, nullable=True)
