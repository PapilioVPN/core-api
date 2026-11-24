"""Customer profile record operations for the administrator panel."""

from collections.abc import Sequence
from typing import Protocol

from ...domain.dtos.records import ProfileCreate, ProfileUpdate
from ...domain.models.records import CustomerModel


class ICustomerService(Protocol):
    async def create(self, data: ProfileCreate) -> CustomerModel: ...

    async def get_by_id(self, id: int) -> CustomerModel: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CustomerModel]: ...

    async def update(self, id: int, data: ProfileUpdate) -> CustomerModel: ...
