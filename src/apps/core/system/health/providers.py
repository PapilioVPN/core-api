"""APP-scoped health probes and focused services."""

from dishka import Provider, Scope, provide

from src.apps.core.system.health.app.interfaces import health as contracts
from src.apps.core.system.health.app.services.pg import PostgresHealthService
from src.apps.core.system.health.app.services.public import PublicHealthService
from src.apps.core.system.health.app.services.redis import RedisHealthService
from src.apps.core.system.health.infra.ping.pg import PostgresPing
from src.apps.core.system.health.infra.ping.redis import RedisPing


class HealthInfraProvider(Provider):
    scope = Scope.APP

    postgres = provide(PostgresPing, scope=Scope.APP)
    redis = provide(RedisPing, scope=Scope.APP)


class HealthServicesProvider(Provider):
    scope = Scope.APP

    public = provide(
        PublicHealthService,
        provides=contracts.IPublicHealthService,
        scope=Scope.APP,
    )
    postgres = provide(
        PostgresHealthService,
        provides=contracts.IPostgresHealthService,
        scope=Scope.APP,
    )
    redis = provide(
        RedisHealthService,
        provides=contracts.IRedisHealthService,
        scope=Scope.APP,
    )
