"""PostgreSQL storage for reusable volume definitions."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from papilio.schemas.results import PagedType
from sqlmodel import col

from src.apps.shop.volumes.domain.enums.records import VolumeMode
from src.apps.shop.volumes.domain.models.records import VolumeModel
from src.apps.shop.volumes.infra.pg.tables import VolumeTable


class VolumeRepository(PGIdentifiedRepository[VolumeModel]):
    table = VolumeTable

    async def list(
        self, *, limit: int, offset: int, mode: VolumeMode | None
    ) -> PagedType[VolumeModel]:
        """Read an ID-ordered page with an optional mode filter.

        Args:
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            mode: Requested kind of volume, when supplied.

        Returns:
            Matching rows with their total before pagination.
        """
        where = () if mode is None else (col(self.table.mode) == mode,)
        page = await self.get_page(
            order_by=[col(self.table.id).asc()],
            limit=limit,
            offset=offset,
            where=where,
        )
        return page
