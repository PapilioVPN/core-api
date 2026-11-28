"""Persist immutable Xray revisions and remove unreferenced records."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from sqlalchemy import ColumnElement, and_, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped
from sqlmodel import col

from src.apps.network.xray.assignments.infra.pg.tables import (
    XrayDesiredRevisionTable,
)
from src.apps.network.xray.instances.infra.pg.tables import (
    XrayRestartRolloutTable,
    XrayStartTable,
)
from src.shared.infra.pg.order import (
    display_position_changes,
    lock_display_positions,
)

from ....domain.enums.removal import XrayRevisionRemovalStatus
from ....domain.models.records import XrayRevisionModel
from ....domain.results.removal import XrayRevisionRemoval
from ..tables import XrayRevisionTable


def _unreferenced(id: Mapped[int]) -> ColumnElement[bool]:
    return and_(
        ~select(1)
        .where(col(XrayDesiredRevisionTable.revision_id) == id)
        .exists(),
        ~select(1).where(col(XrayStartTable.revision_id) == id).exists(),
        ~select(1)
        .where(col(XrayRestartRolloutTable.revision_id) == id)
        .exists(),
    )


class XrayRevisionRepository(PGIdentifiedRepository[XrayRevisionModel]):
    table = XrayRevisionTable

    async def insert(self, data: XrayRevisionModel) -> int | None:
        """Insert one sealed revision without rewriting an existing digest.

        Args:
            data: Timestamped revision with prepared ciphertext and digest.

        Returns:
            The inserted ID, or None if matching bytes are already registered.
        """
        stmt = (
            insert(self.table)
            .values(data.to_row())
            .on_conflict_do_nothing(constraint="uq_xray_revisions_digest")
            .returning(col(self.table.id))
        )
        result = await self.uow.execute(stmt)
        revision_id = result.scalar_one_or_none()
        return revision_id

    async def lock_sort_positions(
        self, ids: tuple[int, ...]
    ) -> dict[int, int]:
        """Read selected positions and serialize concurrent ordering writes.

        Args:
            ids: Distinct requested revision identities.

        Returns:
            Present revision IDs and their effective display positions.
        """
        table = self.table
        stmt = lock_display_positions(
            col(table.sort_order), col(table.id), ids
        )
        result = await self.uow.execute(stmt)
        return {id: position for id, position in result.tuples()}

    async def set_sort_positions(self, positions: dict[int, int]) -> None:
        """Apply changed positions from two bound PostgreSQL arrays.

        Args:
            positions: Locked revision IDs and their new display positions.
        """
        table = self.table
        ordering = display_position_changes(positions)
        stmt = (
            update(table)
            .where(col(table.id) == ordering.c.id)
            .values(sort_order=ordering.c.sort_position)
            .execution_options(synchronize_session=False)
        )
        await self.uow.execute(stmt)

    async def remove_unreferenced_by_id(
        self, id: int
    ) -> XrayRevisionRemovalStatus:
        """Remove one revision while holding its lock against new references.

        Args:
            id: Stable revision identity.

        Returns:
            The deletion result, including absence or a retained reference.
        """
        identity = col(self.table.id)
        stmt = select(identity).where(identity == id).with_for_update()
        locked = await self.uow.execute(stmt)
        status = XrayRevisionRemovalStatus.NOT_FOUND
        if locked.scalar_one_or_none() is not None:
            stmt = (
                delete(self.table)
                .where(identity == id, _unreferenced(identity))
                .returning(identity)
                .execution_options(synchronize_session=False)
            )
            removed = await self.uow.execute(stmt)
            status = (
                XrayRevisionRemovalStatus.DELETED
                if removed.scalar_one_or_none() is not None
                else XrayRevisionRemovalStatus.IN_USE
            )
        return status

    async def remove_unreferenced_by_ids(
        self, ids: tuple[int, ...]
    ) -> tuple[XrayRevisionRemoval, ...]:
        """Lock a bounded selection in ID order and delete its unused rows.

        Args:
            ids: Distinct revision identities in request order.

        Returns:
            One outcome for every supplied identity in the same order.
        """
        identity = col(self.table.id)
        stmt = (
            select(identity)
            .where(identity.in_(ids))
            .order_by(identity)
            .with_for_update()
        )
        result = await self.uow.execute(stmt)
        locked = tuple(result.scalars())
        statuses = dict.fromkeys(ids, XrayRevisionRemovalStatus.NOT_FOUND)
        if locked:
            # This statement sees references committed while acquiring locks.
            stmt = (
                delete(self.table)
                .where(identity.in_(locked), _unreferenced(identity))
                .returning(identity)
                .execution_options(synchronize_session=False)
            )
            removed = await self.uow.execute(stmt)
            statuses.update(
                dict.fromkeys(locked, XrayRevisionRemovalStatus.IN_USE)
            )
            statuses.update(
                dict.fromkeys(
                    removed.scalars(), XrayRevisionRemovalStatus.DELETED
                )
            )
        return tuple(XrayRevisionRemoval(id, statuses[id]) for id in ids)
