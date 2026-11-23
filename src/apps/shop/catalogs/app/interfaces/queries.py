"""Catalog reads exposed to the panel."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.catalogs.domain.models.records import CatalogModel
from src.apps.shop.catalogs.domain.results.details import CatalogDetail
from src.apps.shop.catalogs.domain.results.filters import CatalogOptions
from src.apps.shop.catalogs.domain.results.form import CatalogForm


class ICatalogQuery(Protocol):
    async def get_by_id(self, id: int) -> CatalogDetail: ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[CatalogDetail]: ...

    async def list(self, data: CatalogSearch) -> PagedType[CatalogModel]: ...

    async def options(self, data: CatalogSearch) -> CatalogOptions: ...

    async def form(self, per_page: int) -> CatalogForm: ...
