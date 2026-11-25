"""Bind gateway settings to the native request scope."""

from dishka import Provider, Scope, provide
from papilio.core.config import CryptoConfig, Settings

from .app.interfaces.cache import IGatewayConfigCache
from .app.interfaces.configs import (
    ICryptoGatewayConfigQuery,
    ICryptoGatewayConfigService,
)
from .app.interfaces.services import ICryptoGatewayService
from .app.queries.configs import CryptoGatewayConfigQuery
from .app.services.configs import CryptoGatewayConfigService
from .app.services.crud import CryptoGatewayService
from .infra.pg.repositories.configs import CryptoGatewayConfigRepository
from .infra.pg.repositories.crud import CryptoGatewayRepository
from .infra.redis.repositories.configs import GatewayConfigCache


class CryptoGatewayProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(CryptoGatewayRepository)
    gateways = provide(CryptoGatewayService, provides=ICryptoGatewayService)
    config_repo = provide(CryptoGatewayConfigRepository)
    configs = provide(
        CryptoGatewayConfigService, provides=ICryptoGatewayConfigService
    )
    query = provide(
        CryptoGatewayConfigQuery, provides=ICryptoGatewayConfigQuery
    )
    cache = provide(
        GatewayConfigCache, scope=Scope.APP, provides=IGatewayConfigCache
    )

    @provide(scope=Scope.APP)
    def crypto(self, settings: Settings) -> CryptoConfig:
        """Select the existing deployment encryption settings."""
        crypto = settings.crypto
        if crypto is None:
            raise ValueError("Crypto settings are required")
        return crypto
