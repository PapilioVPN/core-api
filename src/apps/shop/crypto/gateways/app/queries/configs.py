"""Read-through caching for the panel's safe gateway settings."""

from papilio.infra.db.transaction import active_transaction

from ...domain.results.configs import GatewayConfigView
from ..interfaces.cache import IGatewayConfigCache
from ..interfaces.configs import ICryptoGatewayConfigService


class CryptoGatewayConfigQuery:
    ttl = 300

    def __init__(
        self, configs: ICryptoGatewayConfigService, cache: IGatewayConfigCache
    ) -> None:
        """Bind the authoritative configuration reader and its safe cache."""
        self.configs = configs
        self.cache = cache

    async def get(self, id: int) -> GatewayConfigView:
        """Return cached panel settings outside an active transaction."""
        use_cache = active_transaction() is None
        view = await self.cache.find(id) if use_cache else None
        if view is None:
            view = await self.configs.get(id)
            if use_cache:
                await self.cache.store(view, self.ttl)
        return view
