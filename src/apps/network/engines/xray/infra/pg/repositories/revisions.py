"""Insert an immutable revision and read its sealed source."""

from papilio.infra.db.repositories.backends.postgresql import (
    PGIdentifiedRepository,
)
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import col

from ....domain.models.revisions import XrayRevisionModel
from ..tables import XrayRevisionTable


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
