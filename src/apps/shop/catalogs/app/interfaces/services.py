"""Authoritative operations on catalog records."""

from collections.abc import Sequence
from typing import Protocol

from src.apps.shop.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogUpdate,
)
from src.apps.shop.catalogs.domain.models.records import CatalogModel


class ICatalogCRUD(Protocol):
    async def create(self, data: CatalogCreate) -> CatalogModel: ...

    async def update(self, id: int, data: CatalogUpdate) -> CatalogModel: ...

    async def remove(self, id: int) -> CatalogModel: ...

    async def get_by_id(self, id: int) -> CatalogModel: ...

    async def find_by_id(self, id: int) -> CatalogModel | None: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CatalogModel]: ...
