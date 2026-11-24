"""Independent logical file metadata through one native repository."""

from collections.abc import Sequence

from papilio.infra.db.tools.decorators import transactional
from papilio.schemas.results import PagedType
from papilio.tools.checks import IDChecks

from src.apps.core.storage.files.domain.dtos.records import (
    FileBatchRead,
    FileList,
)
from src.apps.core.storage.files.domain.models.records import FileModel
from src.apps.core.storage.files.infra.pg.readers.links import FileLinkReader
from src.apps.core.storage.files.infra.pg.repositories.records import (
    FileRepository,
)


class FileService(IDChecks[FileModel]):
    entity = "File"

    def __init__(self, repo: FileRepository, links: FileLinkReader) -> None:
        """Bind file metadata persistence on the owning request's UoW.

        Args:
            repo: The single native logical file repository.
            links: Registered content URL lookup.
        Returns:
            None.
        """
        self.repo = repo
        self.links = links

    async def find_id_by_url(self, url: str) -> int | None:
        """Resolve a stored file URL without making a network request."""
        id = await self.links.find_id_by_url(url)
        return id

    @transactional
    async def create(self, data: FileModel) -> FileModel:
        """Register a trusted logical reference without changing its content.

        Args:
            data: Prepared content ID, original name and MIME type. The upload
                command owns coordinated existence and authorization checks.
        Returns:
            The persisted file with native identity and timestamps.
        """
        file = await self.repo.create(data)
        return file

    @transactional
    async def create_batch(
        self, data: Sequence[FileModel]
    ) -> Sequence[FileModel]:
        """Register an app-bounded set through one native bulk path.

        Args:
            data: Trusted logical files; the caller bounds the set.
        Returns:
            Created records in unspecified native order, or none for empty
            input. The batch commits atomically or joins its caller's commit.
        """
        files = await self.repo.bulk_create(data)
        return files

    async def get_by_id(self, id: int) -> FileModel:
        """Read required metadata without loading shared content or bytes.

        Args:
            id: Internal logical file identity.
        Returns:
            The stored logical file record.
        Raises:
            NotFoundException: No file has this identity.
        """
        file = await self.repo.get_by_id(id)
        file = self._check_for_id_existence(id, file)
        return file

    async def find_by_id(self, id: int) -> FileModel | None:
        """Read optional logical file metadata.

        Args:
            id: Internal logical file identity.
        Returns:
            The stored record, or None when absent.
        """
        file = await self.repo.get_by_id(id)
        return file

    async def get_by_ids(self, data: FileBatchRead) -> Sequence[FileModel]:
        """Read a bounded identity set through one native selection.

        Args:
            data: One to 100 internal file IDs.
        Returns:
            Found records once each in unspecified order, omitting misses.
        """
        files = await self.repo.get_by_ids(data.ids)
        return files

    async def exists_by_content_id(self, content_id: int) -> bool:
        """Check for logical references without fetching file records.

        Args:
            content_id: Internal physical content ID.
        Returns:
            Whether any logical file references the content.
        """
        referenced = await self.repo.exists_by_content_id(content_id)
        return referenced

    async def get_referenced_content_ids(
        self, content_ids: Sequence[int]
    ) -> Sequence[int]:
        """Read only referenced IDs from a caller-bounded set.

        Args:
            content_ids: Trusted candidate IDs; empty input is allowed.
        Returns:
            Used IDs once each in ascending order; empty input performs no I/O.
        """
        referenced = await self.repo.get_referenced_content_ids(content_ids)
        return referenced

    async def list(self, query: FileList) -> PagedType[FileModel]:
        """List file metadata with application-owned pagination conversion.

        Args:
            query: Native paging, exact content/MIME filters and literal
                case-insensitive original-name substring.
        Returns:
            ID-ordered files with their filtered total, even on empty pages.
            Shared content records and bytes are not loaded.
        """
        page = await self.repo.list(
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
            content_id=query.content_id,
            original_name=query.original_name,
            mime_type=query.mime_type,
        )
        return page
