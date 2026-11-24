"""Prepared record registration and metadata reads, without file transfer."""

from collections.abc import Sequence
from typing import Protocol

from papilio.schemas.results import PagedType

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.files.domain.dtos.records import (
    FileBatchRead,
    FileList,
)
from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.files.domain.models.records import FileModel


class IFileContentService(Protocol):
    """Own physical content records through one repository.

    Registration persists trusted, prepared location/hash/size values; it does
    not store bytes, select a provider or perform deduplication. Writes commit
    independently or join the caller's native transaction. Batch registration
    is one atomic bulk operation; a duplicate hash fails with the native
    conflict error rather than reusing a record. Native bulk result ordering
    is unspecified.
    Logical references and physical deletion have separate lifecycle owners.
    """

    async def create(self, data: FileContentModel) -> FileContentModel:
        """Register prepared content metadata, without file I/O.

        Args:
            data: Trusted content hash, size and original destination.

        Returns:
            The persisted content with its generated identity and timestamps.
        """
        ...

    async def create_batch(
        self, data: Sequence[FileContentModel]
    ) -> Sequence[FileContentModel]:
        """Register an app-bounded set atomically through native bulk I/O.

        Args:
            data: Trusted prepared records in requested insertion order.

        Returns:
            Created records with unspecified order; empty input yields none.
        """
        ...

    async def get_by_id(self, id: int) -> FileContentModel:
        """Read required metadata; absence raises native not-found (404).

        Args:
            id: Internal content identity.

        Returns:
            The content record without loading file references or bytes.
        """
        ...

    async def find_by_id(self, id: int) -> FileContentModel | None:
        """Read optional metadata.

        Args:
            id: Internal content identity.

        Returns:
            The content record, or None when absent.
        """
        ...

    async def find_by_sha256(self, sha256: str) -> FileContentModel | None:
        """Find the original content across all destinations by exact digest.

        Args:
            sha256: Trusted digest, without case conversion or normalization.

        Returns:
            The stored content, or None when absent. No dedup write occurs.
        """
        ...

    async def exists_by_sha256(self, sha256: str) -> bool:
        """Check an exact hash without loading content location/metadata.

        Args:
            sha256: Trusted staged digest, passed unchanged.
        Returns:
            Whether content is registered, irrespective of its destination.
        """
        ...

    async def get_by_ids(
        self, ids: Sequence[int]
    ) -> Sequence[FileContentModel]:
        """Read a bounded set through native set I/O.

        Args:
            ids: Caller-bounded internal content IDs.

        Returns:
            Found records once each with unspecified order; missing IDs omit.
        """
        ...

    async def get_by_sha256s(
        self, hashes: Sequence[str]
    ) -> Sequence[FileContentModel]:
        """Read a bounded digest set across all destinations.

        Args:
            hashes: Caller-bounded exact lookup values.

        Returns:
            Found records in ascending ID order; missing/repeated hashes omit.
        """
        ...

    async def exists_by_provider_id(self, provider_id: int) -> bool:
        """Check provider references without fetching content records.

        Args:
            provider_id: Internal connection identity, active or inactive.

        Returns:
            Whether any stored content references the provider.
        """
        ...

    async def get_referenced_provider_ids(
        self, provider_ids: Sequence[int]
    ) -> Sequence[int]:
        """Read only referenced IDs from a caller-bounded candidate set.

        Args:
            provider_ids: Trusted connection IDs; empty input is allowed.

        Returns:
            Used IDs once each, ascending; missing/unreferenced IDs omit.
            Empty input returns an empty sequence without database I/O.
        """
        ...

    async def list(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        backend: StorageBackend | None = None,
        provider_id: int | None = None,
    ) -> PagedType[FileContentModel]:
        """Read a metadata page using app-owned page-to-offset conversion.

        Args:
            page: Trusted positive page number.
            per_page: Caller-bounded page size.
            backend: Optional exact backend filter.
            provider_id: Optional exact provider filter.

        Returns:
            ID-ordered records with their filtered total, even on empty pages.
        """
        ...


class IFileService(Protocol):
    """Own independent logical file records through one repository.

    Prepared registrations reference existing content; coordinated existence
    checks belong to the upload command. Registration changes no physical bytes
    or content metadata. Writes commit independently or join the caller's
    native transaction; batch registration is one atomic bulk operation.
    Business consumers own associations and authorization. This contract does
    not expose rename, deletion, download or upload finalization policy.
    """

    async def create(self, data: FileModel) -> FileModel:
        """Register prepared logical metadata referencing stored content.

        Args:
            data: Trusted content identity, original name and MIME type.

        Returns:
            The persisted logical file with generated identity and timestamps.
        """
        ...

    async def create_batch(
        self, data: Sequence[FileModel]
    ) -> Sequence[FileModel]:
        """Register an app-bounded set atomically through native bulk I/O.

        Args:
            data: Trusted prepared file records in requested insertion order.

        Returns:
            Created records with unspecified order; empty input yields none.
        """
        ...

    async def get_by_id(self, id: int) -> FileModel:
        """Read required metadata; absence raises native not-found (404).

        Args:
            id: Internal logical file identity.

        Returns:
            The logical record without loading content records or bytes.
        """
        ...

    async def find_by_id(self, id: int) -> FileModel | None:
        """Read optional metadata.

        Args:
            id: Internal logical file identity.

        Returns:
            The file record, or None when absent.
        """
        ...

    async def get_by_ids(self, data: FileBatchRead) -> Sequence[FileModel]:
        """Read a bounded set through native set I/O.

        Args:
            data: One to 100 internal logical file IDs.

        Returns:
            Found records once each with unspecified order; missing IDs omit.
        """
        ...

    async def exists_by_content_id(self, content_id: int) -> bool:
        """Check logical references without fetching file records.

        Args:
            content_id: Internal physical content identity.

        Returns:
            Whether any logical file references that content.
        """
        ...

    async def get_referenced_content_ids(
        self, content_ids: Sequence[int]
    ) -> Sequence[int]:
        """Read only referenced IDs from a caller-bounded candidate set.

        Args:
            content_ids: Trusted content IDs; empty input is allowed.

        Returns:
            Referenced IDs once each, ascending; absent/unreferenced IDs omit.
            Empty input returns an empty sequence without database I/O.
        """
        ...

    async def list(self, query: FileList) -> PagedType[FileModel]:
        """Read a metadata page using app-owned page-to-offset conversion.

        Args:
            query: Page/per-page, exact content/MIME filters and literal
                case-insensitive original-name substring.

        Returns:
            ID-ordered file records with their filtered total, even on empty
            pages. Content records and bytes are not loaded.
        """
        ...
