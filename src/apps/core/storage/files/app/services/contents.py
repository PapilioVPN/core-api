"""Shared content metadata orchestration through one native repository."""

from collections.abc import Sequence

from papilio.infra.db.tools.conflicts import handle_conflicts
from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.files.infra.pg.repositories.contents import (
    FileContentRepository,
)


class FileContentService(IDChecks[FileContentModel]):
    entity = "FileContent"

    def __init__(self, repo: FileContentRepository) -> None:
        """Bind content persistence on the owning request's UoW.

        Args:
            repo: The single native content repository.
        Returns:
            None.
        """
        self.repo = repo

    @handle_conflicts(entity="FileContent")
    @transactional
    async def create(self, data: FileContentModel) -> FileContentModel:
        """Register trusted metadata without transferring bytes.

        Args:
            data: Prepared hash, size and original storage location.
        Returns:
            The persisted content with native identity and timestamps.
        Raises:
            ConflictException: The hash or identity already exists.
        """
        content = await self.repo.create(data)
        return content

    @handle_conflicts(entity="FileContent")
    @transactional
    async def create_batch(
        self, data: Sequence[FileContentModel]
    ) -> Sequence[FileContentModel]:
        """Register an app-bounded prepared set through one native bulk path.

        Args:
            data: Trusted content records; the caller bounds the set.
        Returns:
            Created records in unspecified native order, or none for empty
            input. The batch commits atomically or joins its caller's commit.
        Raises:
            ConflictException: A duplicate hash or identity rejects the batch.
        """
        contents = await self.repo.bulk_create(data)
        return contents

    async def get_by_id(self, id: int) -> FileContentModel:
        """Read required content metadata without loading references or bytes.

        Args:
            id: Internal content identity.
        Returns:
            The stored record with its original location.
        Raises:
            NotFoundException: The content does not exist.
        """
        content = await self.repo.get_by_id(id)
        content = self._check_for_id_existence(id, content)
        return content

    async def find_by_id(self, id: int) -> FileContentModel | None:
        """Read optional content metadata.

        Args:
            id: Internal content identity.
        Returns:
            The stored record, or None when absent.
        """
        content = await self.repo.get_by_id(id)
        return content

    async def find_by_sha256(self, sha256: str) -> FileContentModel | None:
        """Find an exact digest across all original destinations.

        Args:
            sha256: Trusted digest, passed unchanged.
        Returns:
            The stored content, or None; no bytes or records are created.
        """
        content = await self.repo.find_by_sha256(sha256)
        return content

    async def exists_by_sha256(self, sha256: str) -> bool:
        """Check registration through the focused native EXISTS selection.

        Args:
            sha256: Exact staged digest, without normalization.
        Returns:
            Whether content is registered anywhere; no metadata is loaded.
        """
        exists = await self.repo.exists_by_sha256(sha256)
        return exists

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[FileContentModel]:
        """Read a bounded identity set in one native selection.

        Args:
            ids: Caller-bounded internal content IDs.
        Returns:
            Found records once each in unspecified order, omitting misses.
        """
        contents = await self.repo.get_by_ids(ids)
        return contents

    async def get_by_sha256s(
        self, hashes: Sequence[str]
    ) -> Sequence[FileContentModel]:
        """Read exact digest matches across destinations in one selection.

        Args:
            hashes: Caller-bounded exact lookup values.
        Returns:
            Found content in ascending ID order, omitting misses and repeats.
        """
        contents = await self.repo.get_by_sha256s(hashes)
        return contents

    async def exists_by_provider_id(self, provider_id: int) -> bool:
        """Check whether any content references the connection.

        Args:
            provider_id: Internal connection ID, active or inactive.
        Returns:
            Whether a reference exists, without fetching content records.
        """
        referenced = await self.repo.exists_by_provider_id(provider_id)
        return referenced

    async def get_referenced_provider_ids(
        self, provider_ids: Sequence[int]
    ) -> Sequence[int]:
        """Read only referenced IDs from a caller-bounded set.

        Args:
            provider_ids: Trusted candidate IDs; empty input is allowed.
        Returns:
            Used IDs once each in ascending order; empty input performs no I/O.
        """
        referenced = await self.repo.get_referenced_provider_ids(provider_ids)
        return referenced

    async def list(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        backend: StorageBackend | None = None,
        provider_id: int | None = None,
    ) -> PagedType[FileContentModel]:
        """List metadata with application-owned pagination conversion.

        Args:
            page: Trusted positive page number.
            per_page: Caller-bounded page size.
            backend: Optional exact backend filter.
            provider_id: Optional exact provider filter.
        Returns:
            ID-ordered content and its filtered total, even on empty pages.
        """
        result = await self.repo.list(
            limit=per_page,
            offset=(page - 1) * per_page,
            backend=backend,
            provider_id=provider_id,
        )
        return result
