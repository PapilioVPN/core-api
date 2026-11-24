"""Logical file persistence, reference reads and literal name search."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import select
from sqlmodel import col

from src.apps.core.storage.files.domain.models.records import FileModel
from src.apps.core.storage.files.infra.pg.tables import FileTable


class FileRepository(PGPersistenceRepository[FileModel]):
    table = FileTable

    async def exists_by_content_id(self, content_id: int) -> bool:
        """Check for any logical file referencing content with SELECT EXISTS.

        Args:
            content_id: Exact physical content identity.

        Returns:
            True when any logical file references this content. No file/content
            records are fetched.
        """
        referenced = await self.exists(
            col(self.table.content_id) == content_id
        )
        return referenced

    async def get_referenced_content_ids(
        self, content_ids: Sequence[int]
    ) -> Sequence[int]:
        """Read only referenced content IDs from an app-bounded set.

        Args:
            content_ids: Candidate content identities, bounded by the caller.

        Returns:
            Referenced IDs once each in ascending order, omitting missing and
            unreferenced candidates. Empty input performs no I/O.
        """
        referenced: Sequence[int] = []
        if content_ids:
            stmt = (
                select(col(self.table.content_id))
                .where(col(self.table.content_id).in_(content_ids))
                .distinct()
                .order_by(col(self.table.content_id))
            )
            result = await self.uow.execute(stmt)
            referenced = result.scalars().all()
        return referenced

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        content_id: int | None = None,
        original_name: str | None = None,
        mime_type: str | None = None,
    ) -> PagedType[FileModel]:
        """Read an ID-ordered file page with its filtered total.

        Args:
            limit: Positive maximum number of files to retrieve.
            offset: Nonnegative number of matching files to skip.
            content_id: Exact shared content ID, or no filter when None.
            original_name: Literal case-insensitive substring, or no search.
            mime_type: Exact MIME type, or no filter when None.

        Returns:
            Independent file records and their total before paging. Content
            records and bytes are not loaded; empty pages preserve the total.

        Raises:
            ValueError: Native paging rejects invalid limit/offset bounds.
        """
        stmt = select(self.table).order_by(col(self.table.id))
        if content_id is not None:
            stmt = stmt.where(col(self.table.content_id) == content_id)
        if original_name is not None:
            stmt = stmt.where(
                col(self.table.original_name).icontains(
                    original_name, autoescape=True
                )
            )
        if mime_type is not None:
            stmt = stmt.where(col(self.table.mime_type) == mime_type)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
