"""Payment card record operations in the current request scope."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import CardList
from ...domain.models.records import PaymentCardModel


class IPaymentCardService(Protocol):
    async def create(self, data: PaymentCardModel) -> PaymentCardModel: ...

    async def get_by_id(self, id: int) -> PaymentCardModel: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[PaymentCardModel]: ...

    async def list(self, query: CardList) -> PagedType[PaymentCardModel]: ...

    async def update(
        self, id: int, data: PaymentCardModel
    ) -> PaymentCardModel: ...

    async def remove(self, id: int) -> PaymentCardModel: ...
