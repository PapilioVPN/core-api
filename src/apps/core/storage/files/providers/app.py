"""APP-scoped capability dependencies."""

from pathlib import Path

from anyio import Path as AsyncPath
from dishka import Provider, Scope, provide
from papilio.core.config import StorageConfig

from src.apps.core.storage.files.app.executions.downloads import (
    FileDownloadExecution,
)
from src.apps.core.storage.files.app.executions.uploads import (
    FileUploadExecution,
)
from src.apps.core.storage.files.app.interfaces.downloads import (
    IFileDownload,
    IFileDownloadExecution,
)
from src.apps.core.storage.files.app.interfaces.local import ILocalFileStorage
from src.apps.core.storage.files.app.interfaces.private import IPrivateFiles
from src.apps.core.storage.files.app.interfaces.s3 import IS3FileStorage
from src.apps.core.storage.files.app.interfaces.uploads import (
    IFileUpload,
    IFileUploadExecution,
)
from src.apps.core.storage.files.app.pipelines.downloads import (
    FileDownloadPipeline,
)
from src.apps.core.storage.files.app.pipelines.private import PrivateFiles
from src.apps.core.storage.files.app.pipelines.uploads import (
    FileUploadPipeline,
)
from src.apps.core.storage.files.infra.local import LocalFileStorage
from src.apps.core.storage.files.infra.s3.storage import S3FileStorage
from src.apps.core.storage.files.infra.staging import FileStager
from src.shared.utils.asyncio.threads import ThreadRunner


class StorageFileAppProvider(Provider):
    scope = Scope.APP

    s3 = provide(S3FileStorage, provides=IS3FileStorage, scope=Scope.APP)
    upload_execution = provide(
        FileUploadExecution, provides=IFileUploadExecution, scope=Scope.APP
    )
    upload = provide(FileUploadPipeline, provides=IFileUpload, scope=Scope.APP)
    download_execution = provide(
        FileDownloadExecution, provides=IFileDownloadExecution, scope=Scope.APP
    )
    download = provide(
        FileDownloadPipeline, provides=IFileDownload, scope=Scope.APP
    )

    @provide(scope=Scope.APP, provides=ILocalFileStorage)
    def local(self, config: StorageConfig) -> LocalFileStorage:
        """Bind local publication to the configured destination directory.

        Args:
            config: Native filesystem settings for this application.

        Returns:
            One shared adapter; files and streams remain operation-owned.
        """
        result = LocalFileStorage(root=Path(config.path))
        return result

    @provide(scope=Scope.APP, provides=IPrivateFiles)
    async def private(
        self, config: StorageConfig, stager: FileStager
    ) -> PrivateFiles:
        """Resolve private media using the same shared filesystem settings.

        Args:
            config: Public root and shared staging path.
            stager: Existing bounded upload stager.

        Returns:
            The private file service rooted outside public media.

        Raises:
            ValueError: A private or staging path overlaps public media.
        """
        public = await AsyncPath(config.path).resolve()
        root = await public.with_name(f"{public.name}-private").resolve()
        staging = await AsyncPath(config.temp_dir).resolve()
        if (
            root.is_relative_to(public)
            or public.is_relative_to(root)
            or staging.is_relative_to(public)
        ):
            raise ValueError("Private storage must be outside public media")
        await root.mkdir(mode=0o700, parents=True, exist_ok=True)
        return PrivateFiles(Path(root), stager)

    @provide(scope=Scope.APP)
    async def stager(
        self, config: StorageConfig, threads: ThreadRunner
    ) -> FileStager:
        """Prepare the staging parent and bind the shared thread runner.

        Args:
            config: Native settings containing the temporary parent path.
            threads: Existing application-scoped thread runner.

        Returns:
            One shared stager; each operation owns its temporary child.

        Raises:
            OSError: The configured temporary parent cannot be created.
        """
        directory = Path(config.temp_dir)
        await AsyncPath(directory).mkdir(parents=True, exist_ok=True)
        result = FileStager(threads, directory=directory)
        return result
