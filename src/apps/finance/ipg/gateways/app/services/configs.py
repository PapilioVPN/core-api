"""Own the encrypted provider configuration records."""

from papilio.infra.db.tools.decorators import transactional
from papilio.tools.checks import Checks
from pydantic import JsonValue

from ...domain.enums.records import GatewayKind
from ...domain.models.configs import ConfigModel
from ...infra.pg.repositories.configs import ConfigRepository
from ..decorators.configs import forget_cache
from ..interfaces.cache import IGatewayConfigCache


class ConfigService(Checks[ConfigModel]):
    entity = "GatewayConfig"

    def __init__(
        self, repo: ConfigRepository, cache: IGatewayConfigCache
    ) -> None:
        self.repo = repo
        self.cache = cache

    async def find(self, key: GatewayKind) -> ConfigModel | None:
        """Read the authoritative record for the provider key, if saved."""
        config = await self.repo.find(key)
        return config

    async def create(self, data: ConfigModel) -> ConfigModel:
        """Store the encrypted settings in the gateway creation transaction."""
        config = await self.repo.create(data)
        return config

    @forget_cache.one
    @transactional
    async def replace(
        self, key: GatewayKind, data: dict[str, JsonValue]
    ) -> ConfigModel:
        """Replace the existing configuration and evict it after commit."""
        config = await self.repo.replace(key, data)
        config = self._check_for_existence("key", key, config)
        return config
