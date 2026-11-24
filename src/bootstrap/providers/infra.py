"""Native infrastructure selected by the application configuration."""

from dishka import Provider, Scope, provide
from papilio.core.config import HTTPConfig
from papilio.infra.redis.client import RedisClient
from papilio.providers.db import PGProvider
from papilio.providers.http import HTTPProvider
from papilio.providers.passwords import PasswordProvider
from papilio.providers.redis import RedisProvider

from src.bootstrap.providers.outbox import OutboxProvider
from src.bootstrap.providers.storage import StorageInfraProvider
from src.settings.config import CoreSettings
from src.shared.providers.asyncio import AsyncioProvider


class DisabledRedisProvider(Provider):
    @provide(scope=Scope.APP)
    def redis(self) -> RedisClient | None:
        """Provide an absent Redis client when the feature is disabled."""
        return None


def infra_providers(settings: CoreSettings) -> list[Provider]:
    """Select application-owned infrastructure from native settings."""
    if settings.db is None or settings.crypto is None or settings.jwt is None:
        raise ValueError("Core API requires db, crypto and jwt settings")

    http = settings.http or HTTPConfig(
        max_connections=8,
        max_keepalive_connections=4,
        keepalive_expiry=20,
        timeout=20,
        connect_timeout=5,
    )
    providers: list[Provider] = [
        AsyncioProvider(),
        StorageInfraProvider(settings.storage),
        PGProvider(settings.db),
        HTTPProvider(http.model_copy(update={"follow_redirects": False})),
        OutboxProvider(settings),
        PasswordProvider(settings.crypto.password_salt),
    ]
    if settings.redis is None:
        providers.append(DisabledRedisProvider())
    else:
        providers.append(RedisProvider(settings.redis))
        aliases = Provider(scope=Scope.APP)
        aliases.alias(RedisClient, provides=RedisClient | None)
        providers.append(aliases)
    return providers
