"""Authoritative card transfer settings reads and writes."""

from typing import Protocol

from ...domain.dtos.records import (
    TransferSettingsUpdate,
    TransferSettingsWrite,
)
from ...domain.enums.records import SettingsKey
from ...domain.models.records import TransferSettingsModel


class ITransferSettingsService(Protocol):
    async def find(self, key: SettingsKey) -> TransferSettingsModel | None: ...

    async def save(
        self, key: SettingsKey, data: TransferSettingsWrite
    ) -> TransferSettingsModel: ...

    async def update(
        self, key: SettingsKey, data: TransferSettingsUpdate
    ) -> TransferSettingsModel: ...
