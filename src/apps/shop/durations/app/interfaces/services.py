"""Reusable duration operations shared with other shop capabilities."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.durations.domain.dtos.records import (
    DurationCreate,
    DurationList,
)
from src.apps.shop.durations.domain.models.records import DurationModel


class IDurations(Protocol):
    async def create(self, data: DurationCreate) -> DurationModel: ...

    async def get_by_id(self, id: int) -> DurationModel: ...

    async def list(self, query: DurationList) -> PagedType[DurationModel]: ...
