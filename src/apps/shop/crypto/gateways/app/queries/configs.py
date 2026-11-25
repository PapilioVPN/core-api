"""Read gateway settings through the panel cache."""

from papilio.infra.db.transaction import active_transaction

from ...domain.results.configs import GatewayConfigView
from ..interfaces.cache import IGatewayConfigCache
from ..interfaces.configs import IGatewayConfigService


class GatewayConfigQuery:
    ttl = 300

    def __init__(
        self, service: IGatewayConfigService, cache: IGatewayConfigCache
    ) -> None:
        """Bind the authoritative reader and the optional panel cache."""
        self.service = service
        self.cache = cache

    async def get(self, id: int) -> GatewayConfigView:
        """Read safe settings, bypassing cache in a transaction."""
        use_cache = active_transaction() is None
        view = await self.cache.find(id) if use_cache else None
        if view is None:
            view = await self.service.get(id)
            if use_cache:
                await self.cache.store(view, self.ttl)
        return view
