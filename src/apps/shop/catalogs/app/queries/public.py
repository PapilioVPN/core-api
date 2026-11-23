"""Resolve a visible offer for the customer detail view."""

from papilio.tools.checks import IDChecks

from src.apps.shop.catalogs.domain.results.public import PublicCatalog
from src.apps.shop.catalogs.infra.pg.readers.public import PublicCatalogReader


class PublicCatalogQuery(IDChecks[PublicCatalog]):
    entity = "Catalog"

    def __init__(self, reader: PublicCatalogReader) -> None:
        """Bind the public detail reader.

        Args:
            reader: Offer reader on the request's PostgreSQL UoW.

        Returns:
            None.
        """
        self.reader = reader

    async def get_by_id(self, id: int) -> PublicCatalog:
        """Read a published offer on an active service.

        Args:
            id: Requested catalog identity.

        Returns:
            Public title, price in rials, volume in bytes and duration in days.

        Raises:
            NotFoundException: The offer is absent or hidden.
        """
        offer = await self.reader.get_by_id(id)
        offer = self._check_for_id_existence(id, offer)
        return offer
