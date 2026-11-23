"""PostgreSQL storage for reusable volume definitions."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import text, true
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.shop.products.volumes.domain.models.records import VolumeModel
from src.apps.shop.products.volumes.infra.pg.tables import VolumeTable


class VolumeRepository(PGIdentifiedRepository[VolumeModel]):
    table = VolumeTable

    async def insert(self, data: VolumeModel) -> VolumeModel | None:
        """Try to insert a canonical volume.

        Args:
            data: Validated size in bytes, with no identity assigned.

        Returns:
            The new row, or None if that size already has a canonical row.
        """
        table = self.table
        stmt = (
            insert(table)
            .values(data.to_row())
            .on_conflict_do_nothing(
                index_elements=[col(table.size_bytes)],
                index_where=text("is_canonical"),
            )
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        volume = result.scalar_one_or_none()
        return volume

    async def find_by_size(self, size_bytes: int) -> VolumeModel | None:
        """Read the canonical volume of an exact byte size, if stored."""
        table = self.table
        volume = await self.get_one(
            col(table.is_canonical) == true(),
            col(table.size_bytes) == size_bytes,
        )
        return volume

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        size_bytes: int | None = None,
    ) -> PagedType[VolumeModel]:
        """Read an ID-ordered page with an optional size filter.

        Args:
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            size_bytes: Optional exact size required by the picker, in bytes.

        Returns:
            Matching rows with their total before pagination.
        """
        table = self.table
        where = (
            [col(table.size_bytes) == size_bytes]
            if size_bytes is not None
            else []
        )
        page = await self.get_page(
            order_by=[col(table.id).asc()],
            limit=limit,
            offset=offset,
            where=where,
        )
        return page
