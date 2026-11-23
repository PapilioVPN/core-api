"""Read filtered catalog offers and their current search options."""

from papilio.schemas.results import PagedType

from src.apps.shop.products.catalogs.domain.dtos.search import CatalogSearch
from src.apps.shop.products.catalogs.domain.models.records import CatalogModel
from src.apps.shop.products.catalogs.domain.results.filters import (
    CatalogOptions,
)
from src.apps.shop.products.catalogs.infra.pg.readers.search import (
    CatalogSearchReader,
)


class CatalogSearchQuery:
    def __init__(self, reader: CatalogSearchReader) -> None:
        """Bind SQL search on the current request's UoW."""
        self.reader = reader

    async def search(self, data: CatalogSearch) -> PagedType[CatalogModel]:
        """Read the selected page from current SQL records.

        Args:
            data: Validated filters, paging and sorting.

        Returns:
            Matching records and their total.
        """
        page = await self.reader.search(
            data, limit=data.per_page, offset=(data.page - 1) * data.per_page
        )
        return page

    async def get_options(self, data: CatalogSearch) -> CatalogOptions:
        """Read choices over text matches before paging and filters.

        Args:
            data: Original validated search, including its text.

        Returns:
            Counts and price bounds for the current search text.
        """
        options = await self.reader.options(data.q)
        return options
