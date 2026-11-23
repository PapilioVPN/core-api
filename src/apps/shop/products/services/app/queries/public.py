"""Read services that may be displayed in the storefront."""

from papilio.schemas.results import PagedType

from src.apps.shop.products.services.domain.dtos.public import (
    PublicServiceSearch,
)
from src.apps.shop.products.services.domain.results.public import PublicService
from src.apps.shop.products.services.infra.pg.readers.public import (
    PublicServiceReader,
)


class PublicServiceQuery:
    def __init__(self, reader: PublicServiceReader) -> None:
        """Bind the public service search reader.

        Args:
            reader: Search reader on the request's PostgreSQL UoW.

        Returns:
            None.
        """
        self.reader = reader

    async def search(
        self, data: PublicServiceSearch
    ) -> PagedType[PublicService]:
        """Search the active services customers can select.

        Args:
            data: Validated title query and page selection.

        Returns:
            A page of public service cards and the matching total.
        """
        page = await self.reader.search(
            q=data.q,
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
        )
        return page
