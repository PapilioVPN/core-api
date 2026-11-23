"""Authoritative operations on catalog records."""

from collections.abc import Sequence
from typing import Protocol

from src.apps.shop.products.catalogs.domain.dtos.records import CatalogPatch
from src.apps.shop.products.catalogs.domain.models.records import CatalogModel


class ICatalogCRUD(Protocol):
    async def create(self, data: CatalogModel) -> CatalogModel: ...

    async def update(self, id: int, data: CatalogPatch) -> CatalogModel: ...

    async def remove(self, id: int) -> CatalogModel: ...

    async def get_by_id(self, id: int) -> CatalogModel: ...

    async def find_by_id(self, id: int) -> CatalogModel | None: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CatalogModel]: ...
