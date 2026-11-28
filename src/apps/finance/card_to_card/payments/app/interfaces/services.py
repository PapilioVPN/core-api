"""Registration and review of card payments."""

from datetime import datetime
from typing import Protocol

from ...domain.dtos.records import CardPaymentCreate
from ...domain.dtos.review import CardPaymentReview
from ...domain.models.records import CardPaymentModel


class ICardPaymentService(Protocol):
    async def create(self, data: CardPaymentCreate) -> CardPaymentModel: ...

    async def create_auto(
        self,
        *,
        card_id: int,
        amount: int,
        payable_amount: int,
        code: str,
        expires_at: datetime,
    ) -> CardPaymentModel: ...

    async def reserved_amounts(
        self, *, first: int, last: int, expires_at: datetime
    ) -> set[int]: ...

    async def get_by_id(self, id: int) -> CardPaymentModel: ...

    async def confirm_auto(
        self,
        *,
        transfer_id: int,
        card_id: int,
        amount: int,
        transferred_at: datetime,
    ) -> CardPaymentModel | None: ...

    async def review(
        self, id: int, data: CardPaymentReview
    ) -> CardPaymentModel: ...
