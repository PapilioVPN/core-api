"""Catalog reads exposed to the panel."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.products.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.products.catalogs.domain.models.records import CatalogModel
from src.apps.shop.products.catalogs.domain.results.details import (
    CatalogDetail,
)
from src.apps.shop.products.catalogs.domain.results.filters import (
    CatalogOptions,
)
from src.apps.shop.products.catalogs.domain.results.form import CatalogForm


class ICatalogQuery(Protocol):
    async def get_by_id(self, id: int) -> CatalogDetail: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CatalogDetail]: ...


class ICatalogSearchQuery(Protocol):
    async def search(self, data: CatalogSearch) -> PagedType[CatalogModel]: ...

    async def get_options(self, data: CatalogSearch) -> CatalogOptions: ...


class ICatalogFormQuery(Protocol):
    async def form(self, per_page: int) -> CatalogForm: ...
