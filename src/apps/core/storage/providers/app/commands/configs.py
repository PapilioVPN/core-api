"""Configuration replacement after an authoritative parent lookup."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderConfigService,
    IStorageProviderService,
)
from src.apps.core.storage.providers.domain.dtos.configs import S3Config
from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderConfigModel,
)


class StorageProviderConfigCommand:
    def __init__(
        self,
        providers: IStorageProviderService,
        configs: IStorageProviderConfigService,
    ) -> None:
        """Bind metadata reads and configuration writes on the same UoW.

        Args:
            providers: Authoritative connection metadata service.
            configs: Owning configuration record service.

        Returns:
            None.
        """
        self.providers = providers
        self.configs = configs

    @transactional
    async def update(
        self, provider_id: int, data: S3Config
    ) -> StorageProviderConfigModel:
        """Require the parent connection, then replace its configuration.

        Args:
            provider_id: Exact owning connection identity.
            data: Complete validated replacement settings, forwarded unchanged.

        Returns:
            Updated configuration with its parent identity preserved.

        Raises:
            NotFoundException: The parent or its configuration is absent.
        """
        await self.providers.get_by_id(provider_id)
        configuration = await self.configs.update(provider_id, data)
        return configuration
