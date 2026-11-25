"""Bind gateway account operations to the native container."""

from dishka import Provider, Scope, provide
from papilio.core.config import CryptoConfig, Settings

from .app.interfaces.cache import IGatewayConfigCache
from .app.interfaces.configs import IGatewayConfigQuery, IGatewayConfigService
from .app.interfaces.services import ICryptoGatewayService
from .app.queries.configs import GatewayConfigQuery
from .app.services.configs import GatewayConfigService
from .app.services.crud import CryptoGatewayService
from .infra.pg.repositories.configs import GatewayConfigRepository
from .infra.pg.repositories.crud import CryptoGatewayRepository
from .infra.redis.repositories.configs import GatewayConfigCache


class GatewayProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoGatewayRepository)
    gateways = provide(CryptoGatewayService, provides=ICryptoGatewayService)
    config_repo = provide(GatewayConfigRepository)
    configs = provide(GatewayConfigService, provides=IGatewayConfigService)
    query = provide(GatewayConfigQuery, provides=IGatewayConfigQuery)
    cache = provide(
        GatewayConfigCache, scope=Scope.APP, provides=IGatewayConfigCache
    )

    @provide(scope=Scope.APP)
    def crypto(self, settings: Settings) -> CryptoConfig:
        """Expose the existing deployment encryption settings."""
        crypto = settings.crypto
        if crypto is None:
            raise ValueError("Crypto settings are required")
        return crypto
