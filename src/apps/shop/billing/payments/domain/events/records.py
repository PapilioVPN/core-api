"""Identity sent with a finalized payment decision."""

from typing import Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType

from ..models.records import PaymentModel


class PaymentEvent(BaseDTO):
    payment_id: IdType

    @classmethod
    def from_record(cls, record: PaymentModel) -> Self:
        return cls(payment_id=record.id)
