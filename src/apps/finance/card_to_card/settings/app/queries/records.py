"""Read card transfer settings with the panel cache."""

from papilio.infra.db.transaction import active_transaction

from ...domain.enums.records import SettingsKey
from ...domain.models.records import TransferSettingsModel
from ..interfaces.cache import ITransferSettingsCache
from ..interfaces.services import ITransferSettingsService


class TransferSettingsQuery:
    ttl = 300

    def __init__(
        self, settings: ITransferSettingsService, cache: ITransferSettingsCache
    ) -> None:
        self.settings = settings
        self.cache = cache

    async def get(self, key: SettingsKey) -> TransferSettingsModel:
        """Use read-through caching for the panel outside SQL transactions.

        Args:
            key: Settings record to read.

        Returns:
            The saved settings, or the defaults without persisting them.
        """
        use_cache = active_transaction() is None
        settings = await self.cache.find(key) if use_cache else None
        if settings is None:
            settings = await self.settings.find(key)
            if use_cache and settings is not None:
                await self.cache.store(settings, self.ttl)
        return (
            settings
            if settings is not None
            else TransferSettingsModel(key=key)
        )
