"""Receipt creation event."""

from typing import Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType

from ..models.records import ReceiptModel


class ReceiptCreated(BaseDTO):
    receipt_id: IdType

    @classmethod
    def from_record(cls, record: ReceiptModel) -> Self:
        return cls(receipt_id=record.id)
