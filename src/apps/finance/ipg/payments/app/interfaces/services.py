"""The owning record operations for IPG payments."""

from typing import Protocol

from ...domain.models.records import PaymentModel
from ...domain.results.link import ProviderLink


class IPaymentService(Protocol):
    async def create(self, data: PaymentModel) -> PaymentModel: ...

    async def get_by_id(self, id: int) -> PaymentModel: ...

    async def save_link(self, id: int, link: ProviderLink) -> PaymentModel: ...
