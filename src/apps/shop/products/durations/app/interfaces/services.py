"""Reusable duration operations shared with other shop capabilities."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.products.durations.domain.dtos.records import (
    DurationCreate,
    DurationList,
)
from src.apps.shop.products.durations.domain.models.records import (
    DurationModel,
)


class IDurationCRUD(Protocol):
    async def create(self, data: DurationCreate) -> DurationModel: ...

    async def get_by_id(self, id: int) -> DurationModel: ...

    async def find_by_id(self, id: int) -> DurationModel | None: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[DurationModel]: ...

    async def list(self, query: DurationList) -> PagedType[DurationModel]: ...
