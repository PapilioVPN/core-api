"""Own short native SQL requests around file transfer."""

from dishka import AsyncContainer
from papilio.infra.db.tools.decorators import transactional
from papilio.infra.scopes import Inject, request_scoped

from src.apps.core.storage.configs.app.interfaces.services import (
    IStorageConfigService,
)
from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.files.app.interfaces.services import (
    IFileContentService,
    IFileService,
)
from src.apps.core.storage.files.app.validators.uploads import (
    FileUploadValidation,
)
from src.apps.core.storage.files.domain.dtos.uploads import FileUpload
from src.apps.core.storage.files.domain.models.contents import FileContentModel
from src.apps.core.storage.files.domain.models.records import FileModel
from src.apps.core.storage.files.domain.results.uploads import (
    FileUploadDestination,
    FileUploadResult,
)
from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderConfigService,
)


class FileUploadExecution:
    def __init__(self, container: AsyncContainer) -> None:
        """Bind native scope ownership without retaining request resources.

        Args:
            container: Application container used by native request_scoped.
        Returns:
            None.
        """
        self.container = container

    @request_scoped
    async def prepare(
        self,
        sha256: str,
        *,
        contents: IFileContentService = Inject(),
        configs: IStorageConfigService = Inject(),
        providers: IStorageProviderConfigService = Inject(),
    ) -> FileUploadDestination | None:
        """Resolve a new destination and release SQL before physical transfer.

        Args:
            sha256: Digest produced by the owning staging operation.
            contents: Native request-owned content service.
            configs: Native request-owned global destination service.
            providers: Typed active connection service on the same request.
        Returns:
            None for registered content; otherwise a local or materialized S3
            destination. Existing content needs no current selection/provider.
        Raises:
            NotFoundException: New content has no selection or active provider.
            ValidationException: The active S3 configuration is unusable.
        """
        destination = None
        if not await contents.exists_by_sha256(sha256):
            backend = await configs.get_backend()
            connection = None
            if backend is StorageBackend.S3:
                connection = await providers.get_active_connection()
            destination = FileUploadDestination(s3_connection=connection)
        return destination

    @request_scoped
    @transactional
    async def complete(
        self,
        data: FileUpload,
        *,
        sha256: str,
        published: FileContentModel | None,
        contents: IFileContentService = Inject(),
        files: IFileService = Inject(),
    ) -> FileUploadResult:
        """Commit content registration and a logical file together.

        Args:
            data: Validated name and declared MIME from the upload owner.
            sha256: Staged content digest, independent of the destination.
            published: Metadata of newly published bytes, including their
                original S3 location; None when no new publication occurred.
            contents: Fresh native request-owned content service.
            files: Logical file service sharing the same native request/UoW.
        Returns:
            A committed logical reference and the original content URL,
            without changing its destination or reading additional settings.
        Raises:
            ConflictException: No content or new publication exists, or another
                registration wins the SHA-256 unique constraint.
            ValidationException: Existing content has no recorded access URL.
            Exception: Failure before commit rolls back both registrations.
                Published bytes remain untouched for later explicit recovery.
        """
        content = await contents.find_by_sha256(sha256)
        if content is None:
            published = FileUploadValidation.published_content(
                sha256, published
            )
            content = await contents.create(published)
        url = FileUploadValidation.content_url(content)
        file = await files.create(
            FileModel(
                content_id=content.id,
                original_name=data.original_name,
                mime_type=data.mime_type,
            )
        )
        result = FileUploadResult(file=file, url=url)
        return result
