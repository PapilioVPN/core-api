"""Card payment creation, review and confirmation commands."""

from typing import Protocol

from ...domain.dtos.records import AutoPaymentCreate, CardPaymentCreate
from ...domain.dtos.review import CardPaymentReview
from ...domain.models.records import CardPaymentModel


class IAutoPaymentCommand(Protocol):
    async def create(self, data: AutoPaymentCreate) -> CardPaymentModel: ...


class IManualPaymentCommand(Protocol):
    async def create(self, data: CardPaymentCreate) -> CardPaymentModel: ...


class IConfirmTransferCommand(Protocol):
    async def confirm(self, transfer_id: int) -> CardPaymentModel | None: ...


class IReviewPaymentCommand(Protocol):
    async def review(
        self, id: int, data: CardPaymentReview
    ) -> CardPaymentModel: ...
