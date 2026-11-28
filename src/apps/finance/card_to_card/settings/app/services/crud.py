"""Read and edit the authoritative card transfer policy."""

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import Checks

from ...domain.dtos.records import (
    TransferSettingsUpdate,
    TransferSettingsWrite,
    validate_window,
)
from ...domain.enums.records import SettingsKey
from ...domain.models.records import TransferSettingsModel
from ...infra.pg.repositories.crud import TransferSettingsRepository
from ..decorators.records import forget_cache
from ..interfaces.cache import ITransferSettingsCache


class TransferSettingsService(Checks[TransferSettingsModel]):
    def __init__(
        self, repo: TransferSettingsRepository, cache: ITransferSettingsCache
    ) -> None:
        self.repo = repo
        self.cache = cache

    async def find(self, key: SettingsKey) -> TransferSettingsModel | None:
        """Read the current policy directly from PostgreSQL.

        Args:
            key: Settings record to read.

        Returns:
            The saved settings, or None before the first save.
        """
        settings = await self.repo.find_by_key(key)
        return settings

    @forget_cache.one
    @transactional
    async def save(
        self, key: SettingsKey, data: TransferSettingsWrite
    ) -> TransferSettingsModel:
        """Save the panel's policy and evict its cached record.

        Args:
            key: Settings record to create or update.
            data: Validated toggle, digit count and matching window in minutes.

        Returns:
            The saved settings, created on the first save.
        """
        settings = await self.repo.save(
            TransferSettingsModel(
                key=key,
                auto_confirm=data.auto_confirm,
                digits=data.digits,
                window_minutes=data.window_minutes,
            )
        )
        return settings

    @forget_cache.one
    @transactional
    async def update(
        self, key: SettingsKey, data: TransferSettingsUpdate
    ) -> TransferSettingsModel:
        """Apply only the supplied fields and validate the resulting policy.

        Args:
            key: Settings record to create or update.
            data: Validated patch, including an explicit null to clear the
                matching window.

        Returns:
            The complete valid settings after the update.

        Raises:
            ValidationException: No fields were supplied, or the resulting
                policy enables auto confirmation without a matching window.
        """
        changes = self._check_not_empty_dict(data.to_row())
        settings = await self.repo.save(
            TransferSettingsModel(key=key, **changes)
        )
        validate_window(settings.auto_confirm, settings.window_minutes)
        return settings
