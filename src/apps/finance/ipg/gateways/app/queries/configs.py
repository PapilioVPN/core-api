"""Read encrypted provider settings through the keyed cache."""

from papilio.infra.db.transaction import active_transaction
from papilio.tools.checks import Checks

from ...domain.enums.records import GatewayKind
from ...domain.models.configs import ConfigModel
from ..interfaces.cache import IGatewayConfigCache
from ..interfaces.configs import IConfigService


class GatewayConfigQuery(Checks[ConfigModel]):
    entity = "GatewayConfig"
    ttl = 300

    def __init__(
        self, configs: IConfigService, cache: IGatewayConfigCache
    ) -> None:
        self.configs = configs
        self.cache = cache

    async def get(self, key: GatewayKind) -> ConfigModel:
        """Read one configuration by key, using Redis outside transactions.

        Args:
            key: Unique key for the provider's configuration.

        Returns:
            The stored record with encrypted credentials.

        Raises:
            NotFoundException: No configuration exists for this key.
        """
        use_cache = active_transaction() is None
        config = await self.cache.find(key) if use_cache else None
        if config is None:
            config = await self.configs.find(key)
            config = self._check_for_existence("key", key, config)
            if use_cache:
                await self.cache.store(key, config, self.ttl)
        return config
