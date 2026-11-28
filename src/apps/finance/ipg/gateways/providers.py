"""Bind online gateway administration to the native request scope."""

from dishka import Provider, Scope, provide
from papilio.infra.redis.client import RedisClient

from src.settings.config import CoreSettings
from src.shared.infra.redis.configs import ConfigCache

from .app.commands.configs import GatewayConfigCommand
from .app.commands.create import GatewayCreateCommand
from .app.interfaces.cache import IGatewayConfigCache
from .app.interfaces.commands import (
    IGatewayConfigCommand,
    IGatewayCreateCommand,
)
from .app.interfaces.configs import (
    IConfigService,
    IGatewayConfigCodec,
    IGatewayConfigService,
)
from .app.interfaces.queries import IGatewayConfigQuery
from .app.interfaces.services import IGatewayService
from .app.queries.configs import GatewayConfigQuery
from .app.services.configs import ConfigService
from .app.services.credentials import GatewayConfigService
from .app.services.crud import GatewayService
from .domain.enums.records import GatewayKind
from .domain.models.configs import ConfigModel
from .infra.crypto.codec import GatewayConfigCodec
from .infra.pg.repositories.configs import ConfigRepository
from .infra.pg.repositories.crud import GatewayRepository


class GatewaysProvider(Provider):
    scope = Scope.REQUEST

    repo = provide(GatewayRepository)
    config_repo = provide(ConfigRepository)
    config_records = provide(ConfigService, provides=IConfigService)
    gateways = provide(GatewayService, provides=IGatewayService)
    create = provide(GatewayCreateCommand, provides=IGatewayCreateCommand)
    configs = provide(GatewayConfigCommand, provides=IGatewayConfigCommand)

    query = provide(GatewayConfigQuery, provides=IGatewayConfigQuery)
    config_service = provide(
        GatewayConfigService, provides=IGatewayConfigService
    )

    @provide(scope=Scope.APP)
    def cache(self, redis: RedisClient | None) -> IGatewayConfigCache:
        """Bind the provider-kind cache for encrypted configuration."""
        cache = ConfigCache[GatewayKind, ConfigModel](
            redis, "finance:ipg:configs:v1", ConfigModel
        )
        return cache

    @provide(scope=Scope.APP)
    def codec(self, settings: CoreSettings) -> IGatewayConfigCodec:
        """Bind credential encryption to the existing deployment key."""
        return GatewayConfigCodec(settings.crypto)
