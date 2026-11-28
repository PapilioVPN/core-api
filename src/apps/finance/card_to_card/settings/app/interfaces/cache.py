"""Cache operations for keyed transfer settings."""

from typing import Protocol

from ...domain.enums.records import SettingsKey
from ...domain.models.records import TransferSettingsModel


class ITransferSettingsCache(Protocol):
    async def find(self, key: SettingsKey) -> TransferSettingsModel | None: ...

    async def store(
        self, settings: TransferSettingsModel, ttl: int
    ) -> None: ...

    async def forget(self, key: SettingsKey) -> None: ...


class ITransferSettingsCacheOwner(Protocol):
    @property
    def cache(self) -> ITransferSettingsCache: ...
