"""Focused deposit record operations."""

from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import DepositSearch
from ...domain.models.records import DepositModel


class IDepositService(Protocol):
    async def create(self, data: DepositModel) -> DepositModel: ...

    async def link(self, id: int, payment_id: int) -> DepositModel: ...

    async def get(self, id: int) -> DepositModel: ...

    async def search(
        self, query: DepositSearch
    ) -> PagedType[DepositModel]: ...
