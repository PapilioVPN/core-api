"""Read a public catalog offer by its identity."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlmodel import col

from src.apps.shop.catalogs.domain.results.public import PublicCatalog
from src.apps.shop.catalogs.infra.pg.sql.public import visible_catalogs
from src.apps.shop.catalogs.infra.pg.tables import CatalogTable


class PublicCatalogReader(PGReader):
    async def get_by_id(self, id: int) -> PublicCatalog | None:
        """Read one offer that a customer can see.

        Args:
            id: Stored catalog identity.

        Returns:
            Public offer fields, or None when the offer is absent or hidden.
        """
        stmt = visible_catalogs().where(col(CatalogTable.id) == id)
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        offer = PublicCatalog(*row) if row is not None else None
        return offer
