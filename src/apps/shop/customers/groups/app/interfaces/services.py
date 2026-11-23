"""Customer group operations for the administrator panel."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from ...domain.dtos.records import GroupCreate, GroupList, GroupUpdate
from ...domain.models.records import CustomerGroupModel


class IGroupCRUD(Protocol):
    async def create(self, data: GroupCreate) -> CustomerGroupModel: ...

    async def get_by_id(self, id: int) -> CustomerGroupModel: ...

    async def get_by_key(self, key: str) -> CustomerGroupModel: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CustomerGroupModel]: ...

    async def list(
        self, query: GroupList
    ) -> PagedType[CustomerGroupModel]: ...

    async def update(
        self, id: int, data: GroupUpdate
    ) -> CustomerGroupModel: ...

    async def remove(self, id: int) -> CustomerGroupModel: ...
