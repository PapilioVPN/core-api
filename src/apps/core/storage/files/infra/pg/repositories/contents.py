"""Shared content persistence and indexed hash/provider selections."""

from collections.abc import Sequence

from papilio.infra.db.repositories.backends.postgresql import (
    PGPersistenceRepository,
)
from papilio.infra.db.tools.read import fetch_page
from papilio.schemas.results import PagedType
from sqlalchemy import NotNullable, select
from sqlmodel import col

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.files.infra.pg.tables import FileContentTable


class FileContentRepository(PGPersistenceRepository[FileContentModel]):
    table = FileContentTable

    async def exists_by_sha256(self, sha256: str) -> bool:
        """Check an exact digest through the native EXISTS selection.

        Args:
            sha256: Trusted digest, bound without normalization.
        Returns:
            Whether any content row matches, without retrieving its fields.
        """
        exists = await self.exists(col(self.table.sha256) == sha256)
        return exists

    async def find_by_sha256(self, sha256: str) -> FileContentModel | None:
        """Read one stored content by its exact SHA-256.

        Args:
            sha256: Trusted digest, bound without normalization.

        Returns:
            The original content record irrespective of the active destination,
            or None when absent. Logical file references are not loaded.
        """
        content = await self.get_one(col(self.table.sha256) == sha256)
        return content

    async def get_by_sha256s(
        self, hashes: Sequence[str]
    ) -> Sequence[FileContentModel]:
        """Read an app-bounded digest set through one SQL selection.

        Args:
            hashes: Exact digests, bounded by the caller.

        Returns:
            Found content in ascending ID order, omitting missing/repeated
            digests. Empty input performs no I/O.
        """
        contents: Sequence[FileContentModel] = []
        if hashes:
            stmt = (
                select(self.table)
                .where(col(self.table.sha256).in_(hashes))
                .order_by(col(self.table.id))
            )
            result = await self.uow.execute(stmt)
            contents = result.scalars().all()
        return contents

    async def exists_by_provider_id(self, provider_id: int) -> bool:
        """Check for any content referencing a connection with SELECT EXISTS.

        Args:
            provider_id: Exact connection identity, active or inactive.

        Returns:
            True when at least one content record uses the provider. No content
            or file records are fetched.
        """
        referenced = await self.exists(
            col(self.table.provider_id) == provider_id
        )
        return referenced

    async def get_referenced_provider_ids(
        self, provider_ids: Sequence[int]
    ) -> Sequence[int]:
        """Read only used connection IDs from an app-bounded set.

        Args:
            provider_ids: App-bounded candidate connection identities.

        Returns:
            Referenced IDs once each in ascending order. Missing/unreferenced
            candidates omit; empty input performs no I/O.
        """
        referenced: Sequence[int] = []
        if provider_ids:
            stmt = (
                select(NotNullable(col(self.table.provider_id)))
                .where(col(self.table.provider_id).in_(provider_ids))
                .distinct()
                .order_by(col(self.table.provider_id))
            )
            result = await self.uow.execute(stmt)
            referenced = result.scalars().all()
        return referenced

    async def list(
        self,
        *,
        limit: int,
        offset: int = 0,
        backend: StorageBackend | None = None,
        provider_id: int | None = None,
    ) -> PagedType[FileContentModel]:
        """Read an ID-ordered content page with its filtered total.

        Args:
            limit: Positive maximum number of records to retrieve.
            offset: Nonnegative number of matching records to skip.
            backend: Exact local/S3 mechanism, or no filter when None.
            provider_id: Exact connection ID, or no filter when None.

        Returns:
            Stored content and its total before paging; out-of-range pages
            preserve the total. Logical files are not loaded.

        Raises:
            ValueError: Native paging rejects invalid limit/offset bounds.
        """
        stmt = select(self.table).order_by(col(self.table.id))
        if backend is not None:
            stmt = stmt.where(col(self.table.backend) == backend)
        if provider_id is not None:
            stmt = stmt.where(col(self.table.provider_id) == provider_id)
        page = await fetch_page(self.uow, stmt, limit=limit, offset=offset)
        return page
