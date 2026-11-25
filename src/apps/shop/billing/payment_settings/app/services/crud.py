"""Read and manage the Shop payment settings."""

from hashlib import sha256
from secrets import token_urlsafe

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
    async def issue_key(self) -> str:
        """Store a new key digest and return the secret once."""
        key = token_urlsafe(32)
        settings = await self.repo.update_by_id(
            SETTINGS_ID, {"key_hash": sha256(key.encode()).hexdigest()}
        )
        self._check_for_id_existence(SETTINGS_ID, settings)
        return key

    @forget_cache.one
    @transactional
    async def revoke_key(self) -> PaymentSettingsModel:
        """Return the updated settings after clearing the webhook key."""
        settings = await self.repo.update_by_id(
            SETTINGS_ID, {"key_hash": None}
        )
        return self._check_for_id_existence(SETTINGS_ID, settings)
