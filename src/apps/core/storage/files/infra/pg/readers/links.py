"""Resolve registered file addresses to internal download identities."""

from papilio.infra.db.repositories.backends.postgresql import PGReader
from sqlalchemy import select
from sqlmodel import col

from ..tables import FileContentTable, FileTable


class FileLinkReader(PGReader):
    async def find_id_by_url(self, url: str) -> int | None:
        """Read one logical identity for an exact registered content URL."""
        stmt = (
            select(col(FileTable.id))
            .join(
                FileContentTable,
                col(FileContentTable.id) == col(FileTable.content_id),
            )
            .where(col(FileContentTable.url) == url)
            .order_by(col(FileTable.id))
            .limit(1)
        )
        result = await self.uow.execute(stmt)
        id = result.scalar_one_or_none()
        return id
