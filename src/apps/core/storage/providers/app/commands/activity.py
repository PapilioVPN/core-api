"""Atomic coordination of the single active storage connection."""

from papilio.infra.db.tools.decorators import transactional

from src.apps.core.storage.providers.app.interfaces.services import (
    IStorageProviderService,
)
from src.apps.core.storage.providers.domain.dtos.records import (
    StorageProviderActivityUpdate,
)
from src.apps.core.storage.providers.domain.models.records import (
    StorageProviderModel,
)


class StorageProviderActivityCommand:
    def __init__(self, providers: IStorageProviderService) -> None:
        """Bind the owning metadata service on the current request's UoW.

        Args:
            providers: Metadata contract; no repository is imported here.

        Returns:
            None.
        """
        self.providers = providers

    @transactional
    async def update(
        self, id: int, data: StorageProviderActivityUpdate
    ) -> StorageProviderModel:
        """Set activity, atomically replacing a different active connection.

        Args:
            id: Required target connection identity.
            data: True activates the target; False disables only that target.

        Returns:
            Target metadata with its new activity flag. Configuration readiness
            remains the responsibility of usable-connection reads.

        Raises:
            NotFoundException: The target or previous connection vanished.
            ConflictException: A concurrent activation conflicts with this one.
        """
        await self.providers.get_by_id(id)
        if data.is_active:
            active_id = await self.providers.find_active_id()
            if active_id is not None and active_id != id:
                await self.providers.set_active(active_id, is_active=False)
        provider = await self.providers.set_active(
            id, is_active=data.is_active
        )
        return provider
