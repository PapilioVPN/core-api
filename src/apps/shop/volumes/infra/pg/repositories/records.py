"""PostgreSQL storage for reusable volume definitions."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import or_, select, true
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from src.apps.shop.volumes.domain.enums.records import VolumeMode
from src.apps.shop.volumes.domain.models.records import VolumeModel
from src.apps.shop.volumes.infra.pg.tables import VolumeTable


class VolumeRepository(PGIdentifiedRepository[VolumeModel]):
    table = VolumeTable

    async def save(self, data: VolumeModel) -> VolumeModel:
        """Insert one definition or return its existing canonical row.

        Args:
            data: Validated fixed size or range, with no identity assigned.

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
                col(table.mode) == data.mode,
                col(table.size_bytes) == data.size_bytes,
                col(table.min_bytes) == data.min_bytes,
                col(table.max_bytes) == data.max_bytes,
                col(table.step_bytes) == data.step_bytes,
            )
            result = await self.uow.execute(stmt)
            volume = result.scalar_one()
        return volume

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        mode: VolumeMode | None,
        size_bytes: int | None,
    ) -> PagedType[VolumeModel]:
        """Read an ID-ordered page with an optional mode filter.

        Args:
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            mode: Requested kind of volume, when supplied.
            size_bytes: Optional exact size required by the picker, in bytes.

        Returns:
            Matching rows with their total before pagination.
        """
        table = self.table
        where = []
        if mode is not None:
            where.append(col(table.mode) == mode)
        if size_bytes is not None:
            where.append(
                or_(
                    col(table.size_bytes) == size_bytes,
                    (col(table.min_bytes) <= size_bytes)
                    & (col(table.max_bytes) >= size_bytes)
                    & (
                        (size_bytes - col(table.min_bytes))
                        % col(table.step_bytes)
                        == 0
                    ),
                )
            )
        page = await self.get_page(
            order_by=[col(table.id).asc()],
            limit=limit,
            offset=offset,
            where=where,
        )
        return page
