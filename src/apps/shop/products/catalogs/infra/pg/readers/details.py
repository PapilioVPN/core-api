"""Focused PostgreSQL reads for scalar and set catalog details."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlmodel import col

from src.apps.shop.products.catalogs.domain.results.details import (
    CatalogDetail,
)
from src.apps.shop.products.catalogs.infra.pg.sql.details import details
from src.apps.shop.products.catalogs.infra.pg.tables import CatalogTable


class CatalogReader(PGReader):
    async def get_by_id(self, id: int) -> CatalogDetail | None:
        """Read a catalog and its selected volume and duration in one query.

        Args:
            id: Stored catalog identity.

        Returns:
            The catalog and its actual referenced definitions, or None.
        """
        stmt = details().where(col(CatalogTable.id) == id)
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return CatalogDetail(*row) if row is not None else None

    async def get_by_ids(self, ids: Sequence[int]) -> Sequence[CatalogDetail]:
        """Load all existing details for a bounded ID set in one query."""
        if not ids:
            return []
        stmt = details().where(col(CatalogTable.id).in_(ids))
        result = await self.uow.execute(stmt)
        return [CatalogDetail(*row) for row in result.tuples()]
