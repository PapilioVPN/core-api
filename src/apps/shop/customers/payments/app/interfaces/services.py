"""Customer payment records and review operations."""

from collections.abc import Sequence
from typing import Protocol

from ...domain.dtos.records import PaymentReview
from ...domain.models.records import PaymentModel


class IPaymentCRUD(Protocol):
    async def create(self, data: PaymentModel) -> PaymentModel: ...

    async def get_by_id(self, id: int) -> PaymentModel: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[PaymentModel]: ...

    async def review(
        self, id: int, data: PaymentReview, *, reviewer_id: int
    ) -> PaymentModel: ...
