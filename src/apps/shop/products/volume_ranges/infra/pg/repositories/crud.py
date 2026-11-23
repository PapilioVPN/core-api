"""PostgreSQL mutations and scoped reads for volume ranges."""

from collections.abc import Mapping

from papilio.errors.exceptions import ConflictException
from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.schemas.results import PagedType
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import col

from src.apps.shop.products.volume_ranges.domain.models.records import (
    VolumeRangeModel,
)
from src.apps.shop.products.volume_ranges.infra.pg.tables import (
    OVERLAP_CONSTRAINT,
    VolumeRangeTable,
)


def _overlap(service_id: int) -> ConflictException:
    """Report an exclusion conflict for the selected owning service."""
    return ConflictException(
        message="Volume ranges for the same service cannot overlap.",
        message_code="volume_range_overlap",
        unique_dict={"service_id": service_id},
    )


class RangeRepository(PGPersistenceRepository[VolumeRangeModel]):
    table = VolumeRangeTable

    async def create(self, data: VolumeRangeModel) -> VolumeRangeModel:
        """Insert one range using PostgreSQL's exclusion constraint.

        Args:
            data: Prepared range and its stored service identity.

        Returns:
            The stored range, including its assigned ID.

        Raises:
            ConflictException: A range under that service overlaps.
        """
        stmt = (
            insert(self.table)
            .values(data.to_row())
            .on_conflict_do_nothing(constraint=OVERLAP_CONSTRAINT)
            .returning(self.table)
        )
        result = await self.uow.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise _overlap(data.service_id)
        return row

    async def get(self, service_id: int, id: int) -> VolumeRangeModel | None:
        """Read a range within its selected service.

        Args:
            service_id: Required parent service.
            id: Requested range identity.

        Returns:
            The stored range, or None when absent or under another service.
        """
        table = self.table
        row = await self.get_one(
            col(table.service_id) == service_id, col(table.id) == id
        )
        return row

    async def list(
        self,
        service_id: int,
        *,
        limit: int,
        offset: int,
        volume_bytes: int | None = None,
    ) -> PagedType[VolumeRangeModel]:
        """Page through ranges under a single service.

        Args:
            service_id: Required parent service.
            limit: Maximum number of rows.
            offset: Matching rows to skip.
            volume_bytes: Optional selectable volume in bytes.

        Returns:
            Matching ranges and their total ordered by minimum volume and ID.
        """
        table = self.table
        minimum = col(table.min_bytes)
        where = [col(table.service_id) == service_id]
        if volume_bytes is not None:
            where.extend(
                (
                    minimum <= volume_bytes,
                    col(table.max_bytes) >= volume_bytes,
                    ((volume_bytes - minimum) % col(table.step_bytes)) == 0,
                )
            )
        page = await self.get_page(
            where=where,
            order_by=[minimum.asc(), col(table.id).asc()],
            limit=limit,
            offset=offset,
        )
        return page

    async def replace(
        self, service_id: int, id: int, changes: Mapping[str, int | None]
    ) -> VolumeRangeModel | None:
        """Replace the fields under the required service and range identity.

        Args:
            service_id: Required parent service.
            id: Target range identity.
            changes: Validated fields serialized for storage.

        Returns:
            The new stored range, or None when no scoped row matches.

        Raises:
            ConflictException: Another range under that service overlaps.
        """
        table = self.table
        stmt = (
            update(table)
            .where(col(table.service_id) == service_id, col(table.id) == id)
            .values(**changes)
            .returning(table)
            .execution_options(populate_existing=True)
        )
        try:
            result = await self.uow.execute(stmt)
        except IntegrityError as error:
            if getattr(error.orig, "sqlstate", None) == "23P01":
                raise _overlap(service_id) from error
            raise
        row = result.scalar_one_or_none()
        return row

    async def remove_in_service(
        self, service_id: int, id: int
    ) -> VolumeRangeModel | None:
        """Delete one range only under its stored parent.

        Args:
            service_id: Required parent service.
            id: Target range identity.

        Returns:
            The removed range, or None when the scoped row is absent.
        """
        table = self.table
        stmt = (
            delete(table)
            .where(col(table.service_id) == service_id, col(table.id) == id)
            .returning(table)
        )
        result = await self.uow.execute(stmt)
        row = result.scalar_one_or_none()
        return row
