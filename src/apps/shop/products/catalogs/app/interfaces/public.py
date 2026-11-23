"""Public catalog queries for storefront consumers."""

from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.shop.products.catalogs.domain.dtos.public import (
    ServiceCatalogSearch,
)
from src.apps.shop.products.catalogs.domain.results.public import PublicCatalog


class IPublicCatalogQuery(Protocol):
    async def get_by_id(self, id: int) -> PublicCatalog: ...


class IServiceCatalogQuery(Protocol):
    async def search(
        self, service_id: int, data: ServiceCatalogSearch
    ) -> PagedType[PublicCatalog]: ...
