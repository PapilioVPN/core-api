"""Register the application's explicitly configured filesystem settings."""

from dishka import Provider, Scope, alias, provide
from papilio.core.config import StorageConfig

from src.apps.core.storage.files.config import FileStorageConfig


class StorageInfraProvider(Provider):
    def __init__(self, config: FileStorageConfig) -> None:
        """Retain explicit native filesystem settings without opening files.

        Args:
            config: Application-owned local and temporary directory settings.

        Returns:
            None. Resource factories consume this configuration lazily.
        """
        super().__init__()
        self.config = config

    @provide(scope=Scope.APP)
    def storage(self) -> FileStorageConfig:
        """Expose native filesystem settings to capability factories.

        Args:
            None.

        Returns:
            The explicit configuration shared by this application only.
        """
        return self.config

    native_storage = alias(FileStorageConfig, provides=StorageConfig)
