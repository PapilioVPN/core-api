"""Discover the methods available for a requested top-up."""

from typing import Protocol

from ...domain.dtos.methods import DepositMethods
from ...domain.results.methods import PaymentOptions


class IDepositMethodsQuery(Protocol):
    async def list(
        self, customer_id: int, data: DepositMethods
    ) -> PaymentOptions: ...
