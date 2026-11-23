"""Native infrastructure selected by the application configuration."""

from dishka import Provider, Scope, provide
from papilio.core.config import Settings
from papilio.infra.redis.client import RedisClient
from papilio.providers.db import PGProvider
from papilio.providers.passwords import PasswordProvider
from papilio.providers.redis import RedisProvider


class DisabledRedisProvider(Provider):
    @provide(scope=Scope.APP)
    def redis(self) -> RedisClient | None:
        """Provide an absent Redis client when the feature is disabled."""
        return None


def infra_providers(settings: Settings) -> list[Provider]:
    """Select configured native database, password and Redis providers."""
    if settings.db is None or settings.crypto is None or settings.jwt is None:
        raise ValueError("Core API requires db, crypto and jwt settings")

    providers: list[Provider] = [
        PGProvider(settings.db),
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
