"""Catalog writes with service and term resolution."""

from typing import Protocol

from src.apps.shop.products.catalogs.domain.dtos.records import (
    CatalogCreate,
    CatalogUpdate,
)
from src.apps.shop.products.catalogs.domain.models.records import CatalogModel


class ICatalogCommand(Protocol):
    async def create(self, data: CatalogCreate) -> CatalogModel: ...

    async def update(self, id: int, data: CatalogUpdate) -> CatalogModel: ...
