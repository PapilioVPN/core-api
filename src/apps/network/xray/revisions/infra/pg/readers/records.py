"""Read revision metadata without fetching or decrypting source."""

from datetime import datetime

from papilio.infra.db.repositories.backends.postgresql import PGReader
from papilio.schemas.results import PagedType
from sqlalchemy import Select, func, literal, select, tuple_
from sqlalchemy.orm import aliased
from sqlmodel import col

from src.shared.infra.pg.order import cursor_position, display_position

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
        """Read compact choices after the selected display position.

        Args:
            before_id: Last visible revision ID, or None for the first page.
            limit: Maximum number of choices, including any lookahead row.

        Returns:
            Materialized identity, digest and creation time for each choice.
        """
        table = XrayRevisionTable
        id = col(table.id)
        position = display_position(col(table.sort_order), id)
        stmt = select(id, col(table.config_sha256), col(table.created_at))
        if before_id is not None:
            anchor = aliased(table)
            boundary = cursor_position(
                col(anchor.sort_order), col(anchor.id), before_id
            )
            stmt = stmt.where(
                tuple_(position, id) > tuple_(boundary, literal(before_id))
            )
        stmt = stmt.order_by(position, id).limit(limit)
        result = await self.uow.execute(stmt)
        return tuple(XrayRevisionChoice(*row) for row in result.tuples())

    async def for_id(self, id: int) -> XrayRevision | None:
        """Return metadata for one revision, or None for an absent ID."""
        stmt = _metadata().where(col(XrayRevisionTable.id) == id)
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return XrayRevision(*row) if row is not None else None

    async def lock_by_digest(self, digest: str) -> XrayRevision | None:
        """Hold a matching revision until the save transaction commits."""
        stmt = (
            _metadata()
            .where(col(XrayRevisionTable.config_sha256) == digest)
            .with_for_update(key_share=True, read=True)
        )
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return XrayRevision(*row) if row is not None else None

    async def lock_for_reference(self, id: int) -> XrayRevision | None:
        """Read metadata and prevent deletion during reference creation."""
        stmt = (
            _metadata()
            .where(col(XrayRevisionTable.id) == id)
            .with_for_update(key_share=True, read=True)
        )
        result = await self.uow.execute(stmt)
        row = result.tuples().one_or_none()
        return XrayRevision(*row) if row is not None else None

    async def list(
        self, *, limit: int, offset: int
    ) -> PagedType[XrayRevision]:
        """Return one page in the catalog order with its unpaged count.

        Args:
            limit: Maximum rows on the panel page.
            offset: Number of ordered rows to skip.

        Returns:
            One page of credential-free metadata.
        """
        table = XrayRevisionTable
        id = col(table.id)
        stmt = select(func.count()).select_from(table)
        count = await self.uow.execute(stmt)
        stmt = (
            _metadata()
            .order_by(display_position(col(table.sort_order), id), id)
            .limit(limit)
            .offset(offset)
        )
        rows = await self.uow.execute(stmt)
        return PagedType(
            items=[XrayRevision(*row) for row in rows.tuples()],
            total_items=count.scalar_one(),
        )
