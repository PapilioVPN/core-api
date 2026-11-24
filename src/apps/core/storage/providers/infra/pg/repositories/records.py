"""Storage connection metadata through native PostgreSQL persistence."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import select
from sqlmodel import col

from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderModel,
)
from src.apps.core.storage.providers.infra.pg.tables import (
    StorageProviderTable,
)


class StorageProviderRepository(PGPersistenceRepository[StorageProviderModel]):
    table = StorageProviderTable

    async def find_by_key(self, key: str) -> StorageProviderModel | None:
        """Read metadata by its exact case-sensitive key.

        Args:
            key: Stored connection key, bound unchanged in SQL.

        Returns:
            Connection metadata, including inactive records; None if absent.
            Configuration is not loaded.
        """
        provider = await self.get_one(col(self.table.key) == key)
        return provider

    async def get_by_keys(
        self, keys: Sequence[str]
    ) -> Sequence[StorageProviderModel]:
        """Read a bounded set of connection keys in one selection.

        Args:
            keys: Exact keys, with input bounds owned by the app caller.

        Returns:
            Metadata in ascending ID order, omitting absent keys and returning
            repeated keys once. Empty input performs no I/O.
        """
        providers: Sequence[StorageProviderModel] = []
        if keys:
            stmt = (
                select(self.table)
                .where(col(self.table.key).in_(keys))
                .order_by(col(self.table.id))
            )
            result = await self.uow.execute(stmt)
            providers = result.scalars().all()
        return providers

    async def find_active(self) -> StorageProviderModel | None:
        """Read the active connection's metadata without configuration.

        Args:
            None.

        Returns:
            The uniquely active connection, or None if none is active.
        """
        provider = await self.get_one(col(self.table.is_active).is_(True))
        return provider

    async def find_active_id(self) -> int | None:
        """Read only the active connection's identity.

        Args:
            None.

        Returns:
            The active connection ID, or None if none is active. Descriptive
            metadata and configuration are not selected.
        """
        stmt = select(col(self.table.id)).where(
            col(self.table.is_active).is_(True)
        )
        result = await self.uow.execute(stmt)
        provider_id = result.scalar_one_or_none()
        return provider_id

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        title: str | None = None,
        is_active: bool | None = None,
    ) -> PagedType[StorageProviderModel]:
        """Read an ID-ordered metadata page with its filtered total.

        Args:
            limit: Positive maximum number of connections to retrieve.
            offset: Nonnegative number of matching connections to skip.
            title: Literal case-insensitive title substring, or no search.
            is_active: Exact activity flag, or both states when None.

        Returns:
            Metadata and its total before pagination. Empty pages retain the
            matching total; configuration is not loaded.

        Raises:
            ValueError: Native paging rejects invalid limit/offset bounds.
        """
        stmt = select(self.table).order_by(col(self.table.id))
        if title is not None:
            stmt = stmt.where(
                col(self.table.title).icontains(title, autoescape=True)
            )
        if is_active is not None:
            stmt = stmt.where(col(self.table.is_active) == is_active)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
