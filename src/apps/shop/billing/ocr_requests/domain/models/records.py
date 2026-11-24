"""Completed OCR attempts and their originating event identities."""

from papilio.infra.db.schema.entity import PersistenceEntity
from papilio.infra.db.schema.fields import (
    CharField,
    EnumField,
    ForeignKeyField,
)

from src.apps.shop.billing.receipts.domain.enums.extraction import (
    ExtractionStatus,
)


class OCRRequestModel(PersistenceEntity):
    receipt_id: int = ForeignKeyField(
        "tbl_receipts.id", ondelete="RESTRICT", index=True
    )
    event_id: str = CharField(255, unique=True)
    status: ExtractionStatus = EnumField(ExtractionStatus, length=12)
    error_code: str | None = CharField(55, nullable=True, default=None)
