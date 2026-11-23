"""Search the public catalogs of a selected service."""

from papilio.schemas.results import PagedType
from papilio.tools.checks import Checks

from src.apps.shop.catalogs.domain.dtos.public import ServiceCatalogSearch
from src.apps.shop.catalogs.domain.results.public import PublicCatalog
from src.apps.shop.catalogs.infra.pg.readers.service import (
    ServiceCatalogReader,
)


class ServiceCatalogQuery(Checks[PagedType[PublicCatalog]]):
    entity = "Service"

    def __init__(self, reader: ServiceCatalogReader) -> None:
        """Bind the service-scoped catalog search reader.

        Args:
            reader: Search reader on the request's PostgreSQL UoW.

        Returns:
            None.
        """
        self.reader = reader

    async def search(
        self, service_id: int, data: ServiceCatalogSearch
    ) -> PagedType[PublicCatalog]:
        """Search visible offers for one required active service.

        Args:
            service_id: Service selected by the customer.
            data: Validated title, volume, expiry and paging inputs.

        Returns:
            Offers and their matching total, which may be zero.

        Raises:
            NotFoundException: The selected service is absent or inactive.
        """
        page = await self.reader.search(
            service_id,
            data,
            limit=data.per_page,
            offset=(data.page - 1) * data.per_page,
        )
        page = self._check_for_existence("id", service_id, page)
        return page
