"""Read the panel settings from the native read-through cache."""

from papilio.infra.db.transaction import active_transaction

from ...domain.results.records import PaymentSettingsView
from ..interfaces.cache import IPaymentSettingsCache
from ..interfaces.services import IPaymentSettingsService


class PaymentSettingsQuery:
    ttl = 300

    def __init__(
        self, settings: IPaymentSettingsService, cache: IPaymentSettingsCache
    ) -> None:
        """Bind the authoritative settings reader and its panel cache."""
        self.settings = settings
        self.cache = cache

    async def get(self) -> PaymentSettingsView:
        """Read the panel projection, bypassing Redis in a transaction."""
        use_cache = active_transaction() is None
        result = await self.cache.find() if use_cache else None
        if result is None:
            record = await self.settings.get()
            result = PaymentSettingsView.from_record(record)
            if use_cache:
                await self.cache.store(result, self.ttl)
        return result
