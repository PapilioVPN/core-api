"""Read and manage the Shop payment settings."""

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import IDChecks

from ...domain.dtos.records import PaymentSettingsWrite
from ...domain.models.records import PaymentSettingsModel
from ...infra.pg.repositories.crud import PaymentSettingsRepository
from ..decorators.records import forget_cache
from ..interfaces.cache import IPaymentSettingsCache

SETTINGS_ID = 1


class PaymentSettingsService(IDChecks[PaymentSettingsModel]):
    entity = "PaymentSettings"

    def __init__(
        self, repo: PaymentSettingsRepository, cache: IPaymentSettingsCache
    ) -> None:
        """Bind the request's payment settings repository."""
        self.repo = repo
        self.cache = cache

    async def get(self) -> PaymentSettingsModel:
        """Return the global payment policy and active key digest."""
        settings = await self.repo.get_by_id(SETTINGS_ID)
        return self._check_for_id_existence(SETTINGS_ID, settings)

    @forget_cache.one
    @transactional
    async def save(self, data: PaymentSettingsWrite) -> PaymentSettingsModel:
        """Change issuance policy while preserving the webhook credential."""
        settings = await self.repo.update_by_id(SETTINGS_ID, data.to_row())
        return self._check_for_id_existence(SETTINGS_ID, settings)

    @forget_cache.one
    @transactional
    async def set_key_hash(self, digest: str | None) -> PaymentSettingsModel:
        """Replace the prepared key digest, or clear it with None."""
        settings = await self.repo.update_by_id(
            SETTINGS_ID, {"key_hash": digest}
        )
        return self._check_for_id_existence(SETTINGS_ID, settings)
