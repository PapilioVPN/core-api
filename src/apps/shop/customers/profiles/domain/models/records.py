"""Retail customer profiles and their earned group."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BoolField,
    CharField,
    ForeignKeyField,
)


class CustomerModel(PersistenceEntity):
    name: str = CharField(55)
    mobile: str | None = CharField(11, nullable=True, default=None)
    note: str | None = CharField(500, nullable=True, default=None)
    is_blocked: bool = BoolField(default=False)
    group_id: int | None = ForeignKeyField(
        "tbl_customer_groups.id",
        ondelete="RESTRICT",
        nullable=True,
        default=None,
        index=True,
    )
