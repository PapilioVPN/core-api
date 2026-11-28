"""Cache card transfer settings by key in native Redis."""

from papilio.infra.redis.client import RedisClient, resolve
from redis.exceptions import ConnectionError, OutOfMemoryError, TimeoutError

from ....domain.enums.records import SettingsKey
from ....domain.models.records import TransferSettingsModel


class TransferSettingsCache:
    prefix = "finance:card-transfer-settings:v1"

    def __init__(self, redis: RedisClient | None) -> None:
        self.redis = redis

    async def find(self, key: SettingsKey) -> TransferSettingsModel | None:
        """Read the cached settings.

        Args:
            key: Settings record to read.

        Returns:
            The settings, or None on absence or a Redis connection failure.
        """
        settings = None
        if self.redis is not None:
            try:
                raw = await resolve(
                    self.redis.client.get(f"{self.prefix}:{key}")
                )
                if raw is not None:
                    settings = TransferSettingsModel.model_validate_json(raw)
            except (ConnectionError, TimeoutError):
                pass
        return settings

    async def store(self, settings: TransferSettingsModel, ttl: int) -> None:
        """Cache one settings record when Redis is available.

        Args:
            settings: The materialized settings from PostgreSQL.
            ttl: Cache expiry in seconds.

        Returns:
            None.
        """
        if self.redis is not None:
            try:
                await resolve(
                    self.redis.client.set(
                        f"{self.prefix}:{settings.key}",
                        settings.model_dump_json(),
                        ex=ttl,
                    )
                )
            except (ConnectionError, TimeoutError, OutOfMemoryError):
                pass

    async def forget(self, key: SettingsKey) -> None:
        """Remove the cached settings after a successful write.

        Args:
            key: Settings record changed by the successful save.

        Returns:
            None. Unavailable cache entries expire according to their TTL.
        """
        if self.redis is not None:
            try:
                await resolve(self.redis.client.delete(f"{self.prefix}:{key}"))
            except (ConnectionError, TimeoutError):
                pass
