"""Identity published when a bank report has been stored."""

from typing import Self

from papilio.schemas.inputs import BaseDTO
from papilio.types.aliases import IdType

from ..models.records import DepositModel


class DepositReceived(BaseDTO):
    deposit_id: IdType

    @classmethod
    def from_record(cls, record: DepositModel) -> Self:
        return cls(deposit_id=record.id)
