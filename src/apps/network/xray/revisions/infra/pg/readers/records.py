"""Read revision metadata without fetching or decrypting source."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.schemas.results import PagedType
from sqlalchemy import Select, func, select
from sqlmodel import col

from ....domain.results.records import XrayRevision, XrayRevisionChoice
from ..tables import XrayRevisionTable


def _metadata() -> Select[tuple[int, str, int, datetime]]:
    table = XrayRevisionTable
    return select(
        col(table.id),
        col(table.config_sha256),
        col(table.size_bytes),
        col(table.created_at),
    )


class XrayRevisionReader(PGReader):
    async def select_choices(
        self, *, before_id: int | None, limit: int
    ) -> tuple[XrayRevisionChoice, ...]:
        """Read compact choices using the descending primary-key order.

        Args:
            before_id: Exclusive upper ID bound, or None for the latest page.
            limit: Maximum number of choices, including any lookahead row.

        Returns:
            Materialized identity, digest and creation time for each choice.
        """
        table = XrayRevisionTable
        id = col(table.id)
        stmt = select(id, col(table.config_sha256), col(table.created_at))
        if before_id is not None:
            stmt = stmt.where(id < before_id)
        stmt = stmt.order_by(id.desc()).limit(limit)
        result = await self.uow.execute(stmt)
        return tuple(XrayRevisionChoice(*row) for row in result.tuples())

    async def for_id(self, id: int) -> XrayRevision | None:
        """Return metadata for one revision, or None for an absent ID."""
        stmt = _metadata().where(col(XrayRevisionTable.id) == id)
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return XrayRevision(*row) if row is not None else None

    async def for_digest(self, digest: str) -> XrayRevision | None:
        """Find metadata by canonical digest without reading the source."""
        stmt = _metadata().where(
            col(XrayRevisionTable.config_sha256) == digest
        )
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return XrayRevision(*row) if row is not None else None

    async def list(
        self, *, limit: int, offset: int
    ) -> PagedType[XrayRevision]:
        """Return the newest revisions first, with a count before pagination.

        Args:
            limit: Maximum rows on the panel page.
            offset: Number of ordered rows to skip.

        Returns:
            One page of credential-free metadata.
        """
        stmt = select(func.count()).select_from(XrayRevisionTable)
        count = await self.uow.execute(stmt)
        stmt = (
            _metadata()
            .order_by(col(XrayRevisionTable.id).desc())
            .limit(limit)
            .offset(offset)
        )
        rows = await self.uow.execute(stmt)
        return PagedType(
            items=[XrayRevision(*row) for row in rows.tuples()],
            total_items=count.scalar_one(),
        )
