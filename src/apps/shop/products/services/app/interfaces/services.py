"""Service operations for the panel and other shop capabilities."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.products.services.domain.dtos.records import (
    ServiceCreate,
    ServiceList,
    ServiceUpdate,
)
from src.apps.shop.products.services.domain.models.records import ServiceModel


class IShopService(Protocol):
    async def create(self, data: ServiceCreate) -> ServiceModel: ...

    async def get_by_id(self, id: int) -> ServiceModel: ...

    async def find_by_id(self, id: int) -> ServiceModel | None: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[ServiceModel]: ...

    async def list(self, query: ServiceList) -> PagedType[ServiceModel]: ...

    async def update(self, id: int, data: ServiceUpdate) -> ServiceModel: ...

    async def remove(self, id: int) -> ServiceModel: ...
