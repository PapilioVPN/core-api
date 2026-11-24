"""Atomic creation of connection metadata and its configuration."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderConfigService,
    IStorageProviderService,
)
from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderCreate,
)
from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderModel,
)


class StorageProviderCreateCommand:
    def __init__(
        self,
        providers: IStorageProviderService,
        configs: IStorageProviderConfigService,
    ) -> None:
        """Bind record services sharing the current native request UoW.

        Args:
            providers: Connection metadata owner.
            configs: Configuration owner on the same UoW.

        Returns:
            None.
        """
        self.providers = providers
        self.configs = configs

    @transactional
    async def create(
        self, data: StorageProviderCreate, config: S3Config | None = None
    ) -> StorageProviderModel:
        """Create inactive metadata and one configuration atomically.

        Args:
            data: Validated metadata with a user-defined immutable key.
            config: Complete settings, or None to store an empty JSON object.

        Returns:
            Stored metadata with its configuration created in the same
            transaction. An outer caller's transaction remains its owner.

        Raises:
            ConflictException: Another connection already uses the key.
        """
        provider = await self.providers.create(data)
        await self.configs.create(provider.id, config)
        return provider
