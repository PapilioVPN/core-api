"""PostgreSQL storage for reusable volume definitions."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import select, true
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.shop.volumes.domain.models.records import VolumeModel
from src.apps.shop.volumes.infra.pg.tables import VolumeTable


class VolumeRepository(PGIdentifiedRepository[VolumeModel]):
    table = VolumeTable

    async def save(self, data: VolumeModel) -> VolumeModel:
        """Insert one definition or return its existing canonical row.

        Args:
            data: Validated size in bytes, with no identity assigned.

        Returns:
            The canonical row under the shared terms, with its original ID.
        """
        table = self.table
        stmt = (
            insert(table)
            .values(data.to_row())
            .on_conflict_do_nothing()
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        volume = result.scalar_one_or_none()
        if volume is None:
            stmt = select(table).where(
                col(table.is_canonical) == true(),
                col(table.size_bytes) == data.size_bytes,
            )
            result = await self.uow.execute(stmt)
            volume = result.scalar_one()
        return volume

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        size_bytes: int | None,
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
