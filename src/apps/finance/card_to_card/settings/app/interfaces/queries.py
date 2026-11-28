"""The card transfer settings read contract for the panel."""

from typing import Protocol

from ...domain.enums.records import SettingsKey
from ...domain.models.records import TransferSettingsModel


class ITransferSettingsQuery(Protocol):
    async def get(self, key: SettingsKey) -> TransferSettingsModel: ...
