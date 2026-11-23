"""Published or draft shop catalog terms in integer rials."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    BigIntField,
    CharField,
    EnumField,
    ForeignKeyField,
    IntField,
)

from src.apps.shop.catalogs.domain.enums.records import CatalogStatus


class CatalogModel(PersistenceEntity):
    service_id: int = ForeignKeyField("tbl_services.id", ondelete="RESTRICT")
    title: str = CharField(55)
    price: int = BigIntField()
    priority: int = IntField(default=0)
    status: CatalogStatus = EnumField(
        CatalogStatus, length=12, default=CatalogStatus.DRAFT
    )
    volume_id: int | None = ForeignKeyField(
        "tbl_volumes.id", ondelete="RESTRICT", nullable=True, default=None
    )
    duration_id: int | None = ForeignKeyField(
        "tbl_durations.id", ondelete="RESTRICT", nullable=True, default=None
    )
