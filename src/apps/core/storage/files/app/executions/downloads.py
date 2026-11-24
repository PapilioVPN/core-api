"""Resolve recorded file metadata in a short native request."""

from dishka import AsyncContainer
from papilio.infra.scopes import Inject, request_scoped

from src.apps.core.storage.configs.domain.enums.backends import StorageBackend
from src.apps.core.storage.files.app.interfaces.services import (
    IFileContentService,
    IFileService,
)
from src.apps.core.storage.files.app.validators.downloads import (
    FileDownloadValidation,
)
from src.apps.core.storage.files.domain.results.downloads import (
    FileDownloadMetadata,
    PreparedFileDownload,
)
from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderConfigService,
)


class FileDownloadExecution:
    def __init__(self, container: AsyncContainer) -> None:
        """Bind native request execution without retaining SQL resources.

        Args:
            container: Application source used by request_scoped.
        Returns:
            None.
        """
        self.container = container

    @request_scoped
    async def prepare(
        self,
        id: int,
        *,
        files: IFileService = Inject(),
        contents: IFileContentService = Inject(),
        providers: IStorageProviderConfigService = Inject(),
    ) -> PreparedFileDownload:
        """Read a logical file and its original content location.

        Args:
            id: Authorized internal logical file identity.
            files: Native request-owned logical record service.
            contents: Content service sharing the same short native request.
            providers: Configuration service for the recorded S3 connection.
        Returns:
            Materialized metadata and S3 configuration if needed; no stream,
            session or lazy record escapes. Current upload settings are unused.
        Raises:
            NotFoundException: A file/content record or original provider
                configuration is absent.
            ValidationException: Recorded S3 location/configuration is invalid.
        """
        file = await files.get_by_id(id)
        content = await contents.get_by_id(file.content_id)
        metadata = FileDownloadMetadata(
            file_id=file.id,
            original_name=file.original_name,
            mime_type=file.mime_type,
            size_bytes=content.size_bytes,
            sha256=content.sha256,
            storage_key=content.storage_key,
        )
        config = None
        if content.backend is StorageBackend.S3:
            provider_id = FileDownloadValidation.s3_provider_id(
                content.provider_id
            )
            connection = await providers.get_connection(provider_id)
            config = FileDownloadValidation.s3_configuration(
                content, connection.config
            )
        prepared = PreparedFileDownload(metadata=metadata, s3_config=config)
        return prepared
