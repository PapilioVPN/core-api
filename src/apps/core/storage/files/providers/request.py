"""REQUEST-scoped capability dependencies."""

from dishka import Provider, Scope, provide

from src.apps.core.storage.files.app.interfaces.services import (
    IFileContentService,
    IFileService,
)
from src.apps.core.storage.files.app.services.contents import (
    FileContentService,
)
from src.apps.core.storage.files.app.services.records import FileService
from src.apps.core.storage.files.infra.pg.readers.links import FileLinkReader
from src.apps.core.storage.files.infra.pg.repositories.contents import (
    FileContentRepository,
)
from src.apps.core.storage.files.infra.pg.repositories.records import (
    FileRepository,
)


class StorageFileProvider(Provider):
    scope = Scope.REQUEST

    contents = provide(FileContentRepository, scope=Scope.REQUEST)
    files = provide(FileRepository, scope=Scope.REQUEST)
    links = provide(FileLinkReader, scope=Scope.REQUEST)
    content_service = provide(
        FileContentService, provides=IFileContentService, scope=Scope.REQUEST
    )
    file_service = provide(
        FileService, provides=IFileService, scope=Scope.REQUEST
    )
