"""Payment record operations in the current request scope."""

from collections.abc import Sequence
from typing import Protocol

from ...domain.models.records import PaymentModel


class IPaymentService(Protocol):
    async def create(self, data: PaymentModel) -> PaymentModel: ...

    async def get_by_id(self, id: int) -> PaymentModel: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[PaymentModel]: ...
